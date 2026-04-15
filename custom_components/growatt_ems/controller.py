import time
import datetime

class LowPassFilter:
    def __init__(self, tau):
        self.tau = tau
        self.value = 0
        self.last = time.time()

    def apply(self, x):
        now = time.time()
        dt = now - self.last
        self.last = now

        alpha = dt / (self.tau + dt)
        self.value += alpha * (x - self.value)
        return self.value


class PIController:
    def __init__(self, kp, ki, min_out, max_out):
        self.kp = kp
        self.ki = ki
        self.min = min_out
        self.max = max_out
        self.i = 0
        self.last = time.time()

    def update(self, target, actual):
        now = time.time()
        dt = now - self.last
        self.last = now

        error = target - actual
        error = max(-2000, min(2000, error))

        self.i += error * dt
        out = self.kp * error + self.ki * self.i

        if out > self.max:
            out = self.max
            self.i -= error * dt
        elif out < self.min:
            out = self.min
            self.i -= error * dt

        return out


class RampLimiter:
    def __init__(self, rate):
        self.rate = rate
        self.out = 0
        self.last = time.time()

    def apply(self, target):
        now = time.time()
        dt = now - self.last
        self.last = now

        max_step = self.rate * dt
        diff = target - self.out

        if abs(diff) > max_step:
            self.out += max_step if diff > 0 else -max_step
        else:
            self.out = target

        return self.out


class EMSController:

    def __init__(self, hass, modbus):
        self.hass = hass
        self.modbus = modbus

        # CONFIG
        self.MIN_SOC = 10
        self.MAX_SOC = 95
        self.MAX_DISCHARGE = 2800
        self.MAX_CHARGE = 3000

        # STATE
        self.state = {
            "grid": 0,
            "pv": 0,
            "tesla": 0,
            "wallbox": 0,
            "soc": 50,
            "tesla_soc": 50
        }

        # COMPONENTS
        self.grid_filter = LowPassFilter(8)
        self.tesla_filter = LowPassFilter(5)

        self.pi = PIController(0.25, 0.01, -3000, 2800)
        self.ramp = RampLimiter(200)

    async def step(self):

        # -------------------------------
        # INPUT
        # -------------------------------
        pv = -self.state["pv"]
        grid_raw = self.state["grid"]
        grid = self.grid_filter.apply(grid_raw)

        tesla = self.tesla_filter.apply(self.state["tesla"])
        soc = self.state["soc"]
        tesla_soc = self.state["tesla_soc"]
        wallbox = self.state["wallbox"]

        if abs(grid) < 150:
            grid = 0

        # -------------------------------
        # SOC GUARD
        # -------------------------------
        no_discharge = soc <= self.MIN_SOC

        # -------------------------------
        # ENERGY MODEL (BOOST)
        # -------------------------------
        growatt_missing = (100 - soc) / 100 * 32000
        tesla_missing = (100 - tesla_soc) / 100 * 12500

        total = growatt_missing + tesla_missing
        priority = growatt_missing / total if total > 0 else 0.5

        hour = datetime.datetime.now().hour
        time_factor = 1.4 if 11 <= hour <= 16 else 1.0

        if tesla < -200:
            soc_boost = priority * 2500 * time_factor
        else:
            soc_boost = 0

        # -------------------------------
        # MODES
        # -------------------------------
        is_night = pv < 300
        wallbox_active = wallbox > 2500

        # NIGHT WALLBOX
        if is_night and wallbox_active:

            if no_discharge:
                target = 0
            else:
                target = self.MAX_DISCHARGE

            self.pi.i = 0
            self.ramp.rate = 400

        # NIGHT
        elif is_night:

            if tesla > 200:
                target = tesla * (1.1 + 0.3 * priority)
            else:
                target = self.pi.update(grid, 0)

            self.ramp.rate = 300

        # ONLY GROWATT
        elif abs(tesla) < 200:

            target = self.pi.update(grid, 0)

            if abs(grid) < 50:
                target = 0
                self.pi.i *= 0.9

            self.ramp.rate = 120

        # PV MODE
        elif grid < -300:

            target = grid - soc_boost
            self.pi.i = 0
            self.ramp.rate = 250

        # TRANSITION
        else:

            target = self.pi.update(grid, 0) + 0.2 * tesla
            self.ramp.rate = 200

        # -------------------------------
        # LIMIT
        # -------------------------------
        if soc <= self.MIN_SOC:
            target = max(target, 0)

        if soc >= self.MAX_SOC:
            target = min(target, 0)

        target = max(-self.MAX_CHARGE, min(self.MAX_DISCHARGE, target))

        if soc < self.MIN_SOC + 2:
            target *= 0.5

        # -------------------------------
        # RAMP
        # -------------------------------
        target = self.ramp.apply(target)

        # -------------------------------
        # OUTPUT
        # -------------------------------
        if abs(target) < 150:
            await self.modbus.set_idle()

        elif target > 0:
            percent = int((target / self.MAX_DISCHARGE) * 100)
            await self.modbus.set_discharge(percent)

        else:
            percent = int((abs(target) / self.MAX_CHARGE) * 100)
            await self.modbus.set_charge(percent)
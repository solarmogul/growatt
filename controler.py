import datetime

class EMSController:

    def __init__(self, hass):
        self.hass = hass

        self.state = {
            "grid_power": 0,
            "pv_power": 0,
            "tesla_power": 0,
            "wallbox_power": 0,
            "soc": 50,
            "tesla_soc": 50
        }

        self.target = 0

    async def step(self):

        pv = -self.state["pv_power"]
        grid = self.state["grid_power"]
        tesla = self.state["tesla_power"]
        soc = self.state["soc"]

        is_night = pv < 300
        wallbox_active = self.state["wallbox_power"] > 2500

        # -------------------------------
        # NIGHT WALLBOX MODE
        # -------------------------------
        if is_night and wallbox_active:

            if soc <= 10:
                self.target = 0
            else:
                self.target = 2800

        # -------------------------------
        # NIGHT MODE
        # -------------------------------
        elif is_night:

            if tesla > 200:
                self.target = tesla * 1.2
            else:
                self.target = 0

        # -------------------------------
        # PV MODE
        # -------------------------------
        elif grid < -300:
            self.target = grid

        # -------------------------------
        # DEFAULT
        # -------------------------------
        else:
            self.target = 0

        # TODO: Modbus call hier rein
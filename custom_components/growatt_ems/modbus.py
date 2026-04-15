import asyncio
import logging
from pymodbus.client import ModbusTcpClient

_LOGGER = logging.getLogger(__name__)


class GrowattModbus:

    def __init__(self, host="192.168.200.137", port=502, unit=1):
        self.host = host
        self.port = port
        self.unit = unit

        self.client = ModbusTcpClient(self.host, port=self.port)

        self.current_mode = "idle"
        self.last_percent = None

    # ------------------------
    # CONNECTION
    # ------------------------
    def _connect(self):
        if not self.client.connected:
            _LOGGER.warning("Reconnecting Modbus...")
            self.client.connect()

    async def _run(self, func, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args)

    # ------------------------
    # LOW LEVEL
    # ------------------------
    async def write(self, reg, val):
        try:
            self._connect()
            await self._run(self.client.write_register, reg, val, self.unit)
            await asyncio.sleep(0.05)
        except Exception as e:
            _LOGGER.error(f"Write error reg={reg}: {e}")

    async def read(self, reg):
        try:
            self._connect()
            rr = await self._run(
                self.client.read_input_registers,
                reg,
                1,
                self.unit
            )
            if not rr.isError():
                return rr.registers[0]
        except Exception as e:
            _LOGGER.error(f"Read error reg={reg}: {e}")
        return None

    # ------------------------
    # HELPER
    # ------------------------
    def encode_time(self, h, m):
        return (h << 8) | m

    # ------------------------
    # MODE HANDLING
    # ------------------------
    async def deactivate_battery_first(self):
        _LOGGER.debug("Deactivate BatteryFirst")

        await self.write(1102, 0)
        await asyncio.sleep(0.1)

        await self.write(1100, 0)
        await self.write(1101, 0)

    async def deactivate_grid_first(self):
        _LOGGER.debug("Deactivate GridFirst")

        await self.write(1082, 0)
        await asyncio.sleep(0.1)

        await self.write(1080, 0)
        await self.write(1081, 0)

    async def activate_battery_first(self):
        _LOGGER.info("Activate BatteryFirst")

        await self.deactivate_grid_first()

        await self.write(1100, self.encode_time(0, 0))
        await self.write(1101, self.encode_time(23, 59))
        await self.write(1102, 1)

        self.last_percent = None

    async def activate_grid_first(self):
        _LOGGER.info("Activate GridFirst")

        await self.deactivate_battery_first()

        await self.write(1080, self.encode_time(0, 0))
        await self.write(1081, self.encode_time(23, 59))
        await self.write(1082, 1)

        self.last_percent = None

    async def deactivate_all(self):
        await self.deactivate_battery_first()
        await self.deactivate_grid_first()

        self.last_percent = None

    # ------------------------
    # HIGH LEVEL API
    # ------------------------
    async def set_charge(self, percent):

        if self.current_mode != "charge":
            await self.activate_battery_first()
            self.current_mode = "charge"
            await asyncio.sleep(0.3)

        # WRITE OPTIMIZATION
        if percent == self.last_percent:
            return

        _LOGGER.debug(f"CHARGE {percent}%")
        await self.write(1090, percent)

        self.last_percent = percent

    async def set_discharge(self, percent):

        if self.current_mode != "discharge":
            await self.activate_grid_first()
            self.current_mode = "discharge"
            await asyncio.sleep(0.3)

        if percent == self.last_percent:
            return

        _LOGGER.debug(f"DISCHARGE {percent}%")
        await self.write(1070, percent)

        self.last_percent = percent

    async def set_idle(self):

        if self.current_mode != "idle":

            await self.write(1090, 0)
            await asyncio.sleep(0.2)

            await self.write(1070, 0)
            await asyncio.sleep(0.2)

            await self.deactivate_all()

            self.current_mode = "idle"
            await asyncio.sleep(0.2)

        _LOGGER.debug("IDLE")

    # ------------------------
    # SENSOR
    # ------------------------
    async def read_soc(self):
        return await self.read(1014)

    async def read_power(self):
        return await self.read(1020)
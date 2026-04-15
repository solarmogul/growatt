from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from datetime import timedelta

class GrowattCoordinator(DataUpdateCoordinator):

    def __init__(self, hass, controller):
        super().__init__(
            hass,
            logger=None,
            name="growatt_ems",
            update_interval=timedelta(seconds=2)
        )
        self.controller = controller

    async def _async_update_data(self):
        await self.controller.step()
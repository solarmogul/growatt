from homeassistant.components import mqtt

class MQTTHandler:

    def __init__(self, hass, state):
        self.hass = hass
        self.state = state

    async def start(self):

        async def message_received(msg):
            topic = msg.topic
            val = float(msg.payload)

            if topic == "openWB/evu/W":
                self.state["grid_power"] = val

            elif topic == "openWB/pv/W":
                self.state["pv_power"] = val

            elif topic == "openWB/housebattery/W":
                self.state["tesla_power"] = -val

            elif topic == "openWB/lp/1/W":
                self.state["wallbox_power"] = val

        await mqtt.async_subscribe(self.hass, "openWB/#", message_received, 0)
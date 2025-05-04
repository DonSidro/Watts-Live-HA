import voluptuous as vol
import asyncio
import json
from homeassistant import config_entries
from homeassistant.components import mqtt
from homeassistant.const import CONF_NAME
from .const import DOMAIN

class WattsLiveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            serial = user_input[CONF_NAME]
            topic = f"watts/{serial}/measurement"
            event = asyncio.Event()

            try:
                def on_message(msg):
                    try:
                        data = json.loads(msg.payload)
                        if isinstance(data, dict):
                            self.hass.loop.call_soon_threadsafe(event.set)
                    except Exception:
                        pass  # Ignore invalid JSON

                unsub = await mqtt.async_subscribe(self.hass, topic, on_message)
                try:
                    await asyncio.wait_for(event.wait(), timeout=10)
                except asyncio.TimeoutError:
                    errors["base"] = "no_data"
                finally:
                    unsub()
            except Exception as e:
                errors["base"] = "mqtt_error"

            if not errors:
                return self.async_create_entry(
                    title=serial,
                    data={"serial": serial}
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
            }),
            errors=errors
        )

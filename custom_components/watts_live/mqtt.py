
import json
import logging
from homeassistant.components import mqtt
from .const import MQTT_TOPIC_TEMPLATE

_LOGGER = logging.getLogger(__name__)

async def async_subscribe_to_mqtt(hass, serial, callback):
    topic = MQTT_TOPIC_TEMPLATE.format(serial=serial)

    async def message_received(msg):
        try:
            payload = json.loads(msg.payload)
            await callback(payload)
        except json.JSONDecodeError:
            _LOGGER.error("Invalid JSON in MQTT payload")

    await mqtt.async_subscribe(hass, topic, message_received)

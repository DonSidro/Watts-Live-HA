import voluptuous as vol
import asyncio
import json
from homeassistant import config_entries
from homeassistant.components import mqtt, network
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .ble import (
    WattsLiveBleError,
    async_discovered_devices,
    async_provision,
    async_read_status,
)
from .const import (
    BLE_STATUS_ERRORS,
    CONF_ADDRESS,
    CONF_FIRMWARE,
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SAMPLING_INTERVAL,
    CONF_SERIAL,
    CONF_USERNAME,
    DOMAIN,
    LOCAL_BROKER_HOSTS,
    MEASUREMENT_TIMEOUT,
    SAMPLING_INTERVAL_MAX,
    SAMPLING_INTERVAL_MIN,
)

class WattsLiveConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self):
        self._discovered_address = None
        self._provision_input = None
        self._pending_entry = None
        self._retry_step = None

    async def async_step_user(self, user_input=None):
        return self.async_show_menu(
            step_id="user",
            menu_options=["provision", "manual"],
        )

    async def async_step_bluetooth(self, discovery_info):
        """Handle a Watts Live device found by Home Assistant's Bluetooth stack."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._async_abort_entries_match({CONF_ADDRESS: discovery_info.address})

        self._discovered_address = discovery_info.address
        self.context["title_placeholders"] = {"name": discovery_info.name}

        return await self.async_step_provision()

    async def async_step_manual(self, user_input=None):
        errors = {}

        if user_input is not None:
            serial = user_input[CONF_NAME]
            await self.async_set_unique_id(serial)
            self._abort_if_unique_id_configured()

            data = {CONF_SERIAL: serial}
            errors = await self._async_wait_for_measurement(serial)
            if errors.get("base") == "no_data":
                return await self._async_show_no_data(data, "manual")

            if not errors:
                return self.async_create_entry(title=serial, data=data)

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME): str,
            }),
            errors=errors
        )

    async def async_step_provision(self, user_input=None):
        errors = {}

        devices = async_discovered_devices(self.hass)
        if not self._discovered_address and not devices:
            return self.async_abort(reason="no_devices_found")

        if user_input is not None:
            self._provision_input = user_input
            serial = user_input[CONF_SERIAL]
            address = self._discovered_address or user_input[CONF_ADDRESS]

            await self.async_set_unique_id(serial, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            device_info = {}
            try:
                device_info = await async_provision(
                    self.hass,
                    address,
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                    user_input.get(CONF_USERNAME, ""),
                    user_input.get(CONF_PASSWORD, ""),
                    user_input.get(CONF_SAMPLING_INTERVAL),
                )
            except WattsLiveBleError as err:
                errors["base"] = str(err)

            if not errors:
                data = {CONF_SERIAL: serial, CONF_ADDRESS: address}
                if firmware := device_info.get("firmware"):
                    data[CONF_FIRMWARE] = firmware

                errors = await self._async_wait_for_measurement(serial)
                if errors.get("base") == "no_data":
                    # Ask the device why, so the user gets a specific reason.
                    status = await async_read_status(self.hass, address)
                    if status not in BLE_STATUS_ERRORS:
                        # Connected, or the device cannot tell us. It may just
                        # sample less often than we waited.
                        return await self._async_show_no_data(data, "provision")
                    errors["base"] = BLE_STATUS_ERRORS[status]

                if not errors:
                    return self.async_create_entry(title=serial, data=data)

        suggested = (
            user_input
            or self._provision_input
            or await self._async_suggested_broker()
        )

        schema = {}
        if not self._discovered_address:
            schema[vol.Required(CONF_ADDRESS)] = SelectSelector(
                SelectSelectorConfig(
                    options=[
                        {"value": address, "label": label}
                        for address, label in devices.items()
                    ],
                    mode=SelectSelectorMode.DROPDOWN,
                )
            )

        return self.async_show_form(
            step_id="provision",
            data_schema=vol.Schema({
                **schema,
                vol.Required(
                    CONF_SERIAL, description={"suggested_value": suggested.get(CONF_SERIAL)}
                ): str,
                vol.Required(
                    CONF_HOST, description={"suggested_value": suggested.get(CONF_HOST)}
                ): str,
                vol.Required(
                    CONF_PORT,
                    description={"suggested_value": suggested.get(CONF_PORT, 1883)},
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                vol.Optional(
                    CONF_USERNAME,
                    description={"suggested_value": suggested.get(CONF_USERNAME, "")},
                ): str,
                vol.Optional(
                    CONF_PASSWORD,
                    description={"suggested_value": suggested.get(CONF_PASSWORD, "")},
                ): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.PASSWORD)
                ),
                vol.Optional(
                    CONF_SAMPLING_INTERVAL,
                    description={
                        "suggested_value": suggested.get(CONF_SAMPLING_INTERVAL)
                    },
                ): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=SAMPLING_INTERVAL_MIN, max=SAMPLING_INTERVAL_MAX),
                ),
            }),
            errors=errors,
        )

    async def _async_show_no_data(self, data, retry_step):
        self._pending_entry = data
        self._retry_step = retry_step
        return await self.async_step_no_data()

    async def async_step_no_data(self, user_input=None):
        """Offer to add a device that sent nothing while we waited.

        A device sampling less often than MEASUREMENT_TIMEOUT never passes the
        wait, so let the user add it anyway or go back and fix the serial.
        """
        return self.async_show_menu(
            step_id="no_data",
            menu_options=["add_anyway", self._retry_step],
            description_placeholders={
                "serial": self._pending_entry[CONF_SERIAL],
                "timeout": str(MEASUREMENT_TIMEOUT),
            },
        )

    async def async_step_add_anyway(self, user_input=None):
        return self.async_create_entry(
            title=self._pending_entry[CONF_SERIAL], data=self._pending_entry
        )

    async def _async_suggested_broker(self):
        """Pre-fill the form with Home Assistant's own MQTT broker settings."""
        entries = self.hass.config_entries.async_entries(mqtt.DOMAIN)
        if not entries:
            return {}

        data = entries[0].data
        suggested = {
            CONF_PORT: data.get(CONF_PORT, 1883),
            CONF_USERNAME: data.get(CONF_USERNAME, ""),
            CONF_PASSWORD: data.get(CONF_PASSWORD, ""),
        }

        # The device connects over the LAN, so a loopback address or the add-on
        # hostname is useless to it. Suggest Home Assistant's own IP instead.
        host = data.get("broker", "")
        if host.lower() in LOCAL_BROKER_HOSTS:
            host = await network.async_get_source_ip(self.hass) or ""
        suggested[CONF_HOST] = host

        return suggested

    async def _async_wait_for_measurement(self, serial):
        """Wait for the device to publish, so we know it reached the broker."""
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
                await asyncio.wait_for(event.wait(), timeout=MEASUREMENT_TIMEOUT)
            except asyncio.TimeoutError:
                return {"base": "no_data"}
            finally:
                unsub()
        except Exception:
            return {"base": "mqtt_error"}

        return {}

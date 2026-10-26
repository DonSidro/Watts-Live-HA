
from homeassistant.core import callback
from homeassistant.helpers import entity_registry as er

from .const import CONF_SERIAL, DOMAIN

PLATFORMS = ["sensor"]

# Sensor unique IDs before config entry version 1.2, shared by every device.
LEGACY_UNIQUE_ID_PREFIX = "watts_live_"

async def async_migrate_entry(hass, entry):
    if entry.minor_version < 2:
        serial = entry.data[CONF_SERIAL]

        @callback
        def update_unique_id(entity_entry):
            """Scope the unique ID to the device, so several devices can coexist."""
            if not entity_entry.unique_id.startswith(LEGACY_UNIQUE_ID_PREFIX):
                return None
            key = entity_entry.unique_id.removeprefix(LEGACY_UNIQUE_ID_PREFIX)
            return {"new_unique_id": f"{serial}_{key}"}

        await er.async_migrate_entries(hass, entry.entry_id, update_unique_id)
        hass.config_entries.async_update_entry(entry, minor_version=2)

    return True

async def async_setup_entry(hass, entry):
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded

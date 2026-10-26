
import logging

from bleak.exc import BleakCharacteristicNotFoundError, BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components import bluetooth

from .const import (
    BLE_CHAR_HOSTNAME,
    BLE_CHAR_PASSWORD,
    BLE_CHAR_PORT,
    BLE_CHAR_SAMPLING_INTERVAL,
    BLE_CHAR_STATUS,
    BLE_CHAR_USERNAME,
    BLE_NAME_PREFIX,
)

_LOGGER = logging.getLogger(__name__)

# Standard Bluetooth Device Information characteristics, logged to tell card
# variants and firmware versions apart when provisioning fails.
DEVICE_INFO_CHARS = {
    "model": "00002a24-0000-1000-8000-00805f9b34fb",
    "serial": "00002a25-0000-1000-8000-00805f9b34fb",
    "firmware": "00002a26-0000-1000-8000-00805f9b34fb",
    "manufacturer": "00002a29-0000-1000-8000-00805f9b34fb",
}


class WattsLiveBleError(Exception):
    """Raised when provisioning the device over BLE fails."""


def async_discovered_devices(hass):
    """Return connectable Watts Live devices as {address: label}."""
    return {
        info.address: f"{info.name} ({info.address})"
        for info in bluetooth.async_discovered_service_info(hass, connectable=True)
        if info.name and info.name.startswith(BLE_NAME_PREFIX)
    }


async def async_provision(
    hass, address, host, port, username, password, sampling_interval=None
):
    """Write MQTT broker credentials to the device over BLE.

    A sampling interval of None leaves the device's current interval alone.
    Return the device's Device Information strings, such as its firmware
    version, as far as it exposes them.
    """
    ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        raise WattsLiveBleError("device_not_found")

    writes = (
        ("hostname", BLE_CHAR_HOSTNAME, host.encode()),
        ("port", BLE_CHAR_PORT, port.to_bytes(2, "little")),
        ("username", BLE_CHAR_USERNAME, username.encode()),
        ("password", BLE_CHAR_PASSWORD, password.encode()),
    )
    if sampling_interval is not None:
        writes += (
            (
                "sampling interval",
                BLE_CHAR_SAMPLING_INTERVAL,
                sampling_interval.to_bytes(4, "little"),
            ),
        )
    info = await _async_write(ble_device, address, writes, use_services_cache=True)
    if info is not None:
        return info

    # The cached service table did not match the card, so discover it afresh.
    _LOGGER.debug("Retrying %s with a fresh service discovery", address)
    info = await _async_write(ble_device, address, writes, use_services_cache=False)
    if info is None:
        raise WattsLiveBleError("write_failed")
    return info


async def _async_write(ble_device, address, writes, use_services_cache):
    """Write each (name, characteristic, value) to the device.

    Return the device's Device Information strings afterwards, or None if a
    characteristic is missing and the service cache was cleared, so the caller
    can retry once with fresh discovery.
    """
    try:
        client = await establish_connection(
            BleakClientWithServiceCache,
            ble_device,
            address,
            use_services_cache=use_services_cache,
        )
    except (BleakError, TimeoutError) as err:
        _LOGGER.debug("Could not connect to %s: %s", address, err)
        raise WattsLiveBleError("cannot_connect") from err

    try:
        for name, char, value in writes:
            try:
                await client.write_gatt_char(char, value)
            except BleakCharacteristicNotFoundError as err:
                _LOGGER.warning(
                    "Could not find the %s characteristic on %s: %r. Device info: %s. "
                    "Services seen: %s",
                    name,
                    address,
                    err,
                    await _async_read_device_info(client),
                    [
                        f"{service.uuid}: {[c.uuid for c in service.characteristics]}"
                        for service in client.services
                    ],
                )
                if not use_services_cache:
                    raise WattsLiveBleError("write_failed") from err
                await client.clear_cache()
                return None
            except (BleakError, TimeoutError) as err:
                _LOGGER.warning(
                    "Could not write %s (%d bytes, MTU %s) to %s: %r",
                    name,
                    len(value),
                    client.mtu_size,
                    address,
                    err,
                )
                raise WattsLiveBleError("write_failed") from err
        info = await _async_read_device_info(client)
        _LOGGER.debug("Device info for %s: %s", address, info)
    finally:
        try:
            await client.disconnect()
        except (BleakError, TimeoutError) as err:
            _LOGGER.debug("Could not disconnect from %s: %s", address, err)

    return info


async def _async_read_device_info(client):
    """Return the standard Device Information strings the device exposes."""
    info = {}
    for name, char in DEVICE_INFO_CHARS.items():
        try:
            info[name] = (await client.read_gatt_char(char)).decode(errors="replace")
        except (BleakError, TimeoutError):
            continue
    return info


async def async_read_status(hass, address):
    """Return the device's MQTT connection status code, or None if unavailable.

    Older firmware has no status characteristic, and the device turns Bluetooth
    off again 30 minutes after it boots, so this is best effort.
    """
    ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        return None

    try:
        client = await establish_connection(
            BleakClientWithServiceCache, ble_device, address, max_attempts=2
        )
    except (BleakError, TimeoutError) as err:
        _LOGGER.debug("Could not connect to %s to read status: %s", address, err)
        return None

    try:
        value = await client.read_gatt_char(BLE_CHAR_STATUS)
    except (BleakError, TimeoutError) as err:
        _LOGGER.debug("Could not read status from %s: %s", address, err)
        return None
    finally:
        try:
            await client.disconnect()
        except (BleakError, TimeoutError) as err:
            _LOGGER.debug("Could not disconnect from %s: %s", address, err)

    return value[0] if value else None

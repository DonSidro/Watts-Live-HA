
DOMAIN = "watts_live"
MQTT_TOPIC_TEMPLATE = "watts/{serial}/measurement"
SIGNAL_MEASUREMENT = "watts_live_measurement_{serial}"

# BLE provisioning service and characteristics exposed by the Watts Live device.
BLE_NAME_PREFIX = "Watts Live"
BLE_SERVICE_UUID = "a2e1ea9b-01e8-4fe5-9b99-35e9cb44d4b6"
BLE_CHAR_HOSTNAME = "8143af58-b9b8-47ca-911d-ad3564f10d0b"
BLE_CHAR_PORT = "c0175553-1ffd-4eb5-99ca-dc271f4ca050"
BLE_CHAR_USERNAME = "41b6703a-0bac-46b4-a0fa-273f5bf641dc"
BLE_CHAR_PASSWORD = "a59394ed-b929-41a9-81ab-8a16eec6a28c"
BLE_CHAR_STATUS = "1489e2ed-3e77-478c-bec6-34a853d0e8f8"
# UINT32 little endian, in seconds. Watts quote 5 s as the minimum and have
# run cards hourly, so the form stays within that range.
BLE_CHAR_SAMPLING_INTERVAL = "846e613a-ddd1-4584-ae09-b5e903ab9fea"
SAMPLING_INTERVAL_MIN = 5
SAMPLING_INTERVAL_MAX = 3600

# One-byte codes the device reports for its MQTT connection, mapped to the
# config flow error shown when no measurement arrives. Connected (0x00) is not
# an error: the device may just not have sent a reading yet.
BLE_STATUS_ERRORS = {
    0x01: "status_disconnected",
    0x10: "status_dns_error",
    0x20: "status_tcp_error",
    0x30: "status_mqtt_error",
}

# How long setup waits for the first measurement. A device with a longer
# sampling interval can still be added from the step shown after the wait.
MEASUREMENT_TIMEOUT = 30

CONF_ADDRESS = "address"
CONF_SERIAL = "serial"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SAMPLING_INTERVAL = "sampling_interval"
# Firmware version read over Bluetooth during setup. It is not refreshed
# afterwards, because the device turns Bluetooth off 30 minutes after booting.
CONF_FIRMWARE = "firmware"

# Broker addresses that only make sense from Home Assistant itself, never from
# the device's point of view.
LOCAL_BROKER_HOSTS = {"localhost", "127.0.0.1", "::1", "core-mosquitto"}

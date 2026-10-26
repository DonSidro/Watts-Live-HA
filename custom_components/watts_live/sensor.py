
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass
)
from homeassistant.const import (
    UnitOfEnergy,
    UnitOfPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send
)
from .mqtt import async_subscribe_to_mqtt
from .const import CONF_FIRMWARE, DOMAIN, SIGNAL_MEASUREMENT


SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="positive_active_energy",
        translation_key="positive_active_energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:home-import-outline"
    ),
    SensorEntityDescription(
        key="positive_active_power",
        translation_key="positive_active_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="positive_active_power_l1",
        translation_key="positive_active_power_l1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="current_l1",
        translation_key="current_l1",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="voltage_l1",
        translation_key="voltage_l1",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="positive_active_power_l2",
        translation_key="positive_active_power_l2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="current_l2",
        translation_key="current_l2",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="voltage_l2",
        translation_key="voltage_l2",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="positive_active_power_l3",
        translation_key="positive_active_power_l3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="current_l3",
        translation_key="current_l3",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="voltage_l3",
        translation_key="voltage_l3",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="negative_active_energy",
        translation_key="negative_active_energy",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:home-export-outline"
    ),
    SensorEntityDescription(
        key="negative_active_power",
        translation_key="negative_active_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="negative_active_power_l1",
        translation_key="negative_active_power_l1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="negative_active_power_l2",
        translation_key="negative_active_power_l2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    ),
    SensorEntityDescription(
        key="negative_active_power_l3",
        translation_key="negative_active_power_l3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT
    )
]


async def async_setup_entry(hass, entry, async_add_entities):
    serial = entry.data["serial"]
    firmware = entry.data.get(CONF_FIRMWARE)
    sensors = [
        WattsLiveSensor(serial, description, firmware)
        for description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(sensors)

    async def handle_mqtt(payload):
        if isinstance(payload, dict):
            async_dispatcher_send(
                hass, SIGNAL_MEASUREMENT.format(serial=serial), payload
            )

    entry.async_on_unload(await async_subscribe_to_mqtt(hass, serial, handle_mqtt))


class WattsLiveSensor(SensorEntity):
    def __init__(
        self,
        serial: str,
        description: SensorEntityDescription,
        firmware: str | None = None,
    ):
        self.entity_description = description
        self.serial = serial
        self.firmware = firmware
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{serial}_{description.key}"

    async def async_added_to_hass(self):
        # Only entities that are actually added listen, so disabled or removed
        # ones are never asked to write state.
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_MEASUREMENT.format(serial=self.serial),
                self._handle_measurement,
            )
        )

    @callback
    def _handle_measurement(self, payload):
        if self.entity_description.key in payload:
            self.update_value(payload[self.entity_description.key])

    @property
    def translation_key(self):
        return self.entity_description.key

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.serial)},
            "name": "Watts Live",
            "manufacturer": "Watts",
            "model": "Watts Live Energy Monitor",
            "connections": {("mqtt", f"watts/{self.serial}/measurement")},
            "sw_version": self.firmware,
        }

    def update_value(self, value):
        try:
            self._attr_native_value = float(value)
        except (ValueError, TypeError):
            self._attr_native_value = None
        self.async_write_ha_state()

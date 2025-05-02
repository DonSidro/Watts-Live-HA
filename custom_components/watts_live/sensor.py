
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
from .mqtt import async_subscribe_to_mqtt
from .const import DOMAIN


SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="positive_active_energy",
        translation_key="positive_active_energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
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
    sensors = [WattsLiveSensor(serial, description) for description in SENSOR_DESCRIPTIONS]

    async_add_entities(sensors)

    async def handle_mqtt(payload):
        for sensor in sensors:
            if sensor.entity_description.key in payload:
                sensor.update_value(payload[sensor.entity_description.key])

    await async_subscribe_to_mqtt(hass, serial, handle_mqtt)


class WattsLiveSensor(SensorEntity):
    def __init__(self, serial: str, description: SensorEntityDescription):
        self.entity_description = description
        self.serial = serial
        self._state = None
        self._attr_has_entity_name = True
        self._attr_unique_id = f"watts_live_{description.key}"

    @property
    def state(self):
        return self._state
    
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
        }

    def update_value(self, value):
        try:
            self._state = float(value)
        except (ValueError, TypeError):
            self._state = None
        self.async_write_ha_state()

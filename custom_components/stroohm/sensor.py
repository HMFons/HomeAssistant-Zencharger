"""Stroohm sensor."""

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import StroohmConfigEntry
from .const import (
    ID_INSTANTANEOUS_POWER,
    ID_INSTANTANEOUS_POWER_PHASE_1,
    ID_INSTANTANEOUS_POWER_PHASE_2,
    ID_INSTANTANEOUS_POWER_PHASE_3,
    ID_SESSION_ENERGY,
    ID_STATE,
    ID_TOTAL_ENERGY,
)
from .stroohm.energy_sensor import StroohmEnergySensor
from .stroohm.power_sensor import StroohmPowerSensor
from .stroohm.sensor import StroohmSensor

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS = SensorEntityDescription(
    key=ID_STATE,
    translation_key="state",
    name="State",
)
ENERGY_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key=ID_TOTAL_ENERGY,
        translation_key="total",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        name="Total energy",
    ),
    SensorEntityDescription(
        key=ID_SESSION_ENERGY,
        translation_key="session",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        name="Session energy",
    ),
)
POWER_SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key=ID_INSTANTANEOUS_POWER,
        translation_key="instant",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        name="Instantaneous power",
    ),
    SensorEntityDescription(
        key=ID_INSTANTANEOUS_POWER_PHASE_1,
        translation_key="instantPhase1",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        name="Instantaneous power, phase 1",
    ),
    SensorEntityDescription(
        key=ID_INSTANTANEOUS_POWER_PHASE_2,
        translation_key="instantPhase2",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        name="Instantaneous power, phase 2",
    ),
    SensorEntityDescription(
        key=ID_INSTANTANEOUS_POWER_PHASE_3,
        translation_key="instantPhase3",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        name="Instantaneous power, phase 3",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StroohmConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up stroohm sensors based on a config entry."""
    stroohm = entry.runtime_data.websocket

    async_add_entities(
        StroohmEnergySensor(stroohm, description)
        for description in ENERGY_SENSOR_DESCRIPTIONS
    )
    async_add_entities(
        StroohmPowerSensor(stroohm, description)
        for description in POWER_SENSOR_DESCRIPTIONS
    )
    async_add_entities([StroohmSensor(stroohm, SENSOR_DESCRIPTIONS)])

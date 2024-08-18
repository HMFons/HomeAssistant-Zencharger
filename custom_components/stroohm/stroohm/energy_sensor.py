import logging
import math

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTR_REALTIME_POWER

_LOGGER = logging.getLogger(__name__)


class StroohmEnergySensor(CoordinatorEntity, SensorEntity):
    """Base class for all StroohmEnergySensor sensors."""

    def __init__(
        self, coordinator, unique_id, name, attribute, data_name, device_info=None
    ):
        """Initialize the entity"""
        super().__init__(coordinator)
        self._unique_id = unique_id
        self._name = name
        self._attribute = attribute
        self._data_name = data_name
        self._device_info = device_info

    @property
    def device_class(self) -> str:
        return SensorDeviceClass.ENERGY

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def native_value(self) -> float:
        try:
            return self.get_float_value_from_coordinator(self._attribute)
        except StroohmEnergySensorException as e:
            _LOGGER.error(e)
            return None

    @property
    def native_unit_of_measurement(self) -> str:
        return UnitOfEnergy.KILO_WATT_HOUR

    @property
    def state_class(self) -> str:
        return SensorStateClass.TOTAL_INCREASING

    @property
    def device_info(self) -> dict:
        return self._device_info

    def is_producing_at_the_moment(self) -> bool:
        try:
            realtime_power = self.get_float_value_from_coordinator(ATTR_REALTIME_POWER)
            return not math.isclose(realtime_power, 0, abs_tol=0.001)
        except StroohmEnergySensorException as e:
            _LOGGER.info(e)
            return False

    def get_float_value_from_coordinator(self, attribute_name: str) -> float:
        if self.coordinator.data is False:
            raise StroohmEnergySensorException("Coordinator data is False")
        if self._data_name not in self.coordinator.data:
            raise StroohmEnergySensorException(
                f"Attribute {self._data_name} not in coordinator data"
            )
        if self._attribute not in self.coordinator.data[self._data_name]:
            raise StroohmEnergySensorException(
                f"Attribute {attribute_name} not in coordinator data"
            )

        if self.coordinator.data[self._data_name][attribute_name] is None:
            raise StroohmEnergySensorException(
                f"Attribute {attribute_name} has value None"
            )
        elif self.coordinator.data[self._data_name][attribute_name] == "N/A":
            raise StroohmEnergySensorException(
                f"Attribute {attribute_name} has value N/A"
            )

        try:
            return float(self.coordinator.data[self._data_name][attribute_name])
        except ValueError:
            raise StroohmEnergySensorException(
                f"Attribute {self._attribute} has value {self.coordinator.data[self._data_name][attribute_name]} which is not a float"
            )


class StroohmEnergySensorTotalCurrentDay(StroohmEnergySensor):
    pass


class StroohmEnergySensorException(Exception):
    pass

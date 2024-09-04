from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.helpers.entity import EntityDescription

from .entity import StroohmEntity
from .stroohm_websocket import StroohmWebSocket


class StroohmEnergyEntity(StroohmEntity):
    """Base class for all StroohmEnergyEntity entities."""

    def __init__(
        self,
        stroohm: StroohmWebSocket,
        description: EntityDescription,
    ):
        """Initialize the entity"""
        super().__init__(stroohm, description)

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def unit_of_measurement(self):
        return UnitOfEnergy.WATT_HOUR


class StroohmEnergyEntityRealtime(StroohmEnergyEntity):
    pass


class StroohmEnergyEntityRealtimeInWatt(StroohmEnergyEntity):
    @property
    def unit_of_measurement(self):
        return UnitOfPower.WATT

from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfPower
from homeassistant.helpers.entity import EntityDescription

from .entity import StroohmEntity
from .stroohm_websocket import StroohmWebSocket


class StroohmPowerEntity(StroohmEntity):
    """Base class for all StroohmPowerEntity entities."""

    def __init__(
        self,
        stroohm: StroohmWebSocket,
        description: EntityDescription,
    ):
        """Initialize the entity"""
        super().__init__(stroohm, description)

    @property
    def device_class(self):
        return SensorDeviceClass.POWER

    @property
    def unit_of_measurement(self):
        return UnitOfPower.WATT


class StroohmPowerEntityRealtime(StroohmPowerEntity):
    pass


class StroohmPowerEntityRealtimeInWatt(StroohmPowerEntity):
    @property
    def unit_of_measurement(self):
        return UnitOfPower.WATT
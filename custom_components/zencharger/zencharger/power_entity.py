from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfPower
from homeassistant.helpers.entity import EntityDescription

from .entity import ZenchargerEntity
from .zencharger_websocket import ZenchargerWebSocket


class ZenchargerPowerEntity(ZenchargerEntity):
    """Base class for all ZenchargerPowerEntity entities."""

    def __init__(
        self,
        zencharger: ZenchargerWebSocket,
        description: EntityDescription,
    ):
        """Initialize the entity"""
        super().__init__(zencharger, description)

    @property
    def device_class(self):
        return SensorDeviceClass.POWER

    @property
    def unit_of_measurement(self):
        return UnitOfPower.WATT


class ZenchargerPowerEntityRealtime(ZenchargerPowerEntity):
    pass


class ZenchargerPowerEntityRealtimeInWatt(ZenchargerPowerEntity):
    @property
    def unit_of_measurement(self):
        return UnitOfPower.WATT

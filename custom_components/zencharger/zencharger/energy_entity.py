from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import UnitOfEnergy, UnitOfPower
from homeassistant.helpers.entity import EntityDescription

from .entity import ZenchargerEntity
from .zencharger_websocket import ZenchargerWebSocket


class ZenchargerEnergyEntity(ZenchargerEntity):
    """Base class for all ZenchargerEnergyEntity entities."""

    def __init__(
        self,
        zencharger: ZenchargerWebSocket,
        description: EntityDescription,
    ):
        """Initialize the entity"""
        super().__init__(zencharger, description)

    @property
    def device_class(self):
        return SensorDeviceClass.ENERGY

    @property
    def unit_of_measurement(self):
        return UnitOfEnergy.WATT_HOUR


class ZenchargerEnergyEntityRealtime(ZenchargerEnergyEntity):
    pass


class ZenchargerEnergyEntityRealtimeInWatt(ZenchargerEnergyEntity):
    @property
    def unit_of_measurement(self):
        return UnitOfPower.WATT

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityDescription

from .entity import ZenchargerEntity
from .websocket import ZenchargerWebSocket

_LOGGER = logging.getLogger(__name__)


class ZenchargerSensor(ZenchargerEntity, SensorEntity):
    """Base class for all ZenchargerPowerSensor sensors."""

    def __init__(
        self,
        zencharger: ZenchargerWebSocket,
        description: EntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(zencharger, description)

    @callback
    def update_from_latest_data(self) -> None:
        """Fetch new state data for the sensor."""
        raw = self._zencharger.charger[self.entity_description.key]
        self._attr_native_value = raw

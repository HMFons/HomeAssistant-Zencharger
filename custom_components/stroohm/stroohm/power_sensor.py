import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.entity import EntityDescription

from .power_entity import StroohmPowerEntity
from .stroohm_websocket import StroohmWebSocket

_LOGGER = logging.getLogger(__name__)


class StroohmPowerSensor(StroohmPowerEntity, SensorEntity):
    """Base class for all StroohmPowerSensor sensors."""

    def __init__(
        self,
        stroohm: StroohmWebSocket,
        description: EntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(stroohm, description)

    @callback
    def update_from_latest_data(self) -> None:
        """Fetch new state data for the sensor."""
        raw = self._stroohm.charger[self.entity_description.key]
        self._attr_native_value = raw

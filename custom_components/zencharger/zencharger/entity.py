from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity, EntityDescription

from ..const import DOMAIN
from .websocket import ZenchargerWebSocket


class ZenchargerEntity(Entity):
    """Base class for all Zencharger entities."""

    def __init__(
        self,
        zencharger: ZenchargerWebSocket,
        description: EntityDescription,
    ):
        """Initialize the entity"""
        self._zencharger = zencharger
        self.entity_description = description
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "Zencharger")},
            manufacturer="Zencharger",
            name="Zencharger".capitalize(),
        )
        self._attr_unique_id = f"{description.key}"

    @callback
    def _async_update(self) -> None:
        """Update the state."""
        last_data = self._zencharger.charger
        key = self.entity_description.key
        self._attr_available = last_data.get(key) is not None
        self.update_from_latest_data()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                "charger_data_update",
                self._async_update,
            )
        )

        self.update_from_latest_data()

    @callback
    def update_from_latest_data(self) -> None:
        """Update the entity from the latest data."""
        raise NotImplementedError

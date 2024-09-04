"""Custom integration to integrate Zencharger dashboard with Home Assistant."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType

from custom_components.zencharger.zencharger.api import ZenchargerApi
from custom_components.zencharger.zencharger.websocket import WebSocketError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type ZenchargerConfigEntry = ConfigEntry[ZenchargerApi]


async def async_setup(hass: HomeAssistant, _: ConfigType) -> bool:
    """Set up the Zencharger component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Zencharger component from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform.
    hass.add_job(
        hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    )

    api = ZenchargerApi(hass, entry)

    try:
        await api.ws_connect()
    except WebSocketError as err:
        _LOGGER.error("Config entry failed: %s", err)
        raise ConfigEntryNotReady from err

    entry.runtime_data = api

    async def _async_disconnect_websocket(_: Event) -> None:
        await api._websocket.disconnect()

    entry.async_on_unload(
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, _async_disconnect_websocket
        )
    )
    return True

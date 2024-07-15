"""
Custom integration to integrate Stroohm dashboard with Home Assistant.
"""
from homeassistant.core import HomeAssistant, Config
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up the Stroohm component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the Stroohm component from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True

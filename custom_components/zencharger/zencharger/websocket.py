import json
import logging
from threading import Thread

import websocket

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import dispatcher_send

from ..const import (
    CONF_CREDENTIALS,
    CONF_HOST,
    ID_INSTANTANEOUS_POWER,
    ID_INSTANTANEOUS_POWER_PHASE_1,
    ID_INSTANTANEOUS_POWER_PHASE_2,
    ID_INSTANTANEOUS_POWER_PHASE_3,
    ID_SESSION_ENERGY,
    ID_STATE,
    ID_TOTAL_ENERGY,
)

DEFAULT_SOCKET_MIN_RETRY = 15

_LOGGER = logging.getLogger(__name__)


@callback
def async_hydrate_data(data: dict[str, str]) -> dict[str, str]:
    """Hydrate data with addition or normalized data."""
    return {
        ID_TOTAL_ENERGY: data["meterData"]["totalEnergy"],
        ID_SESSION_ENERGY: data["meterData"]["sessionEnergy"],
        ID_INSTANTANEOUS_POWER: sum(data["meterData"]["instantaneousPower"]),
        ID_INSTANTANEOUS_POWER_PHASE_1: data["meterData"]["instantaneousPower"][0],
        ID_INSTANTANEOUS_POWER_PHASE_2: data["meterData"]["instantaneousPower"][1],
        ID_INSTANTANEOUS_POWER_PHASE_3: data["meterData"]["instantaneousPower"][2],
        ID_STATE: data["state"],
    }


class ZenchargerWebSocket:
    """Define a class to handle the Zencharger websocket."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self._hass = hass
        self._host = entry.data[CONF_CREDENTIALS][CONF_HOST]
        self._entry_setup_complete = False
        self._ws_reconnect_delay = DEFAULT_SOCKET_MIN_RETRY
        self.charger: dict[str, str] = {
            ID_INSTANTANEOUS_POWER: "0",
            ID_INSTANTANEOUS_POWER_PHASE_1: "0",
            ID_INSTANTANEOUS_POWER_PHASE_2: "0",
            ID_INSTANTANEOUS_POWER_PHASE_3: "0",
            ID_SESSION_ENERGY: "0",
            ID_STATE: "",
            ID_TOTAL_ENERGY: "0",
        }

    async def ws_connect(self, cookie: str) -> None:
        """Register handlers and connect to the websocket."""

        def on_open(ws) -> None:
            """Define a handler to fire when the websocket is connected."""
            _LOGGER.info("Connected to websocket")
            ws.send('{"action": "subscribe", "topic": "/session/status"}')

        def on_message(ws, message) -> None:
            """Define a handler to fire when the data is received."""

            # TODO: does this need to be threaded?
            def run(*args):
                parsed = json.loads(message)

                # Ignore subscribe
                if parsed["type"] == "result":
                    return

                data = parsed["data"]

                # If data has not changed, don't update:
                if (
                    data["meterData"]["totalEnergy"] == self.charger[ID_TOTAL_ENERGY]
                    and data["state"] == self.charger[ID_STATE]
                ):
                    return

                self.charger = async_hydrate_data(data)
                dispatcher_send(self._hass, "charger_data_update")

            Thread(target=run).start()

        def on_close(ws, close_status_code, close_msg) -> None:
            """Define a handler to fire when the websocket is disconnected."""
            _LOGGER.info("Disconnected from websocket")

        def on_error(ws, error):
            _LOGGER.error(error)

        ws = websocket.WebSocketApp(
            "ws" + self._host[4:] + "/api/v1/ws",
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
            cookie=cookie,
        )
        wst = Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()

    async def ws_disconnect(self) -> None:
        """Disconnect from the websocket."""
        await self.websocket.disconnect()


class WebSocketError(Exception):
    """Define an error related to generic websocket errors."""

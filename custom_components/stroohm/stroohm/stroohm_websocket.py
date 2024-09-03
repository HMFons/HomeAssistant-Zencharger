import logging
from threading import Thread

import websocket

DEFAULT_SOCKET_MIN_RETRY = 15

_LOGGER = logging.getLogger(__name__)


class StroohmWebSocket:
    """Define a class to handle the Stroohm websocket."""

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host
        self._entry_setup_complete = False
        self._ws_reconnect_delay = DEFAULT_SOCKET_MIN_RETRY

    async def ws_connect(self, cookie: str) -> None:
        """Register handlers and connect to the websocket."""

        def on_open(ws) -> None:
            """Define a handler to fire when the websocket is connected."""
            _LOGGER.info("Connected to websocket")
            ws.send('{"action": "subscribe", "topic": "/session/status"}')

        def on_message(ws, message) -> None:
            """Define a handler to fire when the data is received."""
            _LOGGER.info("Message recieved")

            # TODO: does this need to be threaded?
            def run(*args):
                _LOGGER.info(message)

            Thread(target=run).start()

        def on_close(ws, close_status_code, close_msg) -> None:
            """Define a handler to fire when the websocket is disconnected."""
            _LOGGER.info("Disconnected from websocket")

        def on_error(ws, error):
            _LOGGER.error(error)

        ws = websocket.WebSocketApp(
            "ws" + self.host[4:] + "/api/v1/ws",
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

"""API client for Zencharger Dashboard."""

import logging

import httpx
from requests import get

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

<<<<<<< HEAD
=======
from ..const import CONF_CREDENTIALS, CONF_HOST, CONF_PASSWORD

>>>>>>> 4e62ab4 (chore: use parameters as keys)
from .websocket import ZenchargerWebSocket

from .const import ATTR_DATA, ATTR_FAIL_CODE

_LOGGER = logging.getLogger(__name__)


class ZenchargerApi:
    """Api class."""

    @property
    def websocket(self):
        return self._websocket

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self._sessionId = None
<<<<<<< HEAD
        self._host = entry.data["credentials"]["host"]
        self._password = entry.data["credentials"]["password"]
=======
        self._host = entry.data[CONF_CREDENTIALS][CONF_HOST]
        self._password = entry.data[CONF_CREDENTIALS][CONF_PASSWORD]
>>>>>>> 4e62ab4 (chore: use parameters as keys)
        self._websocket = ZenchargerWebSocket(hass, entry)

    async def ws_connect(self):
        if self._sessionId is None:
            self.login()
        await self._websocket.ws_connect(self._sessionId)

    def login(self) -> str:
        """Login to api to get Session id."""

        url = self._host + "/api/v1/auth/login"
        headers = {
            "accept": "application/json",
        }
        body = {
            "Password": self._password,
            "PersistentSession": True,
        }
        try:
            response = httpx.post(url, headers=headers, json=body, timeout=1.5)
            response.raise_for_status()

            if "Set-Cookie" in response.headers:
                self._sessionId = response.headers["Set-Cookie"]
                return response.headers.get("Set-Cookie")

            raise ZenchargerApiError("Could not login with given credentials")
        except Exception as error:
            raise ZenchargerApiError("Could not login with given credentials")

    def status(self) -> str:
        """Get status from API."""

        url = self._host + "/api/v1/auth/status"
        headers = {
            "accept": "application/json",
        }

        try:
            response = get(url, headers=headers, timeout=1.5)
            response.raise_for_status()

            if "Set-Cookie" in response.headers:
                self._sessionId = response.headers["Set-Cookie"]
                return response.headers.get("Set-Cookie")

            raise ZenchargerApiError("Could not get status")
        except Exception as error:
            raise ZenchargerApiError("Could not get status")

    def _do_call(self, url: str, body: dict):
        if self._sessionId is None:
            self.login()

        headers = {
            "accept": "application/json",
            "xsrf-token": self._sessionId,
        }

        try:
            response = httpx.post(url, headers=headers, json=body, timeout=5)
            response.raise_for_status()
            json_data = response.json()

            # Session Expired code?
            if ATTR_FAIL_CODE in json_data and json_data[ATTR_FAIL_CODE] == 305:
                # token expired
                self._sessionId = None
                return self._do_call(url, body)

            if ATTR_FAIL_CODE in json_data and json_data[ATTR_FAIL_CODE] != 0:
                raise ZenchargerApiError(
                    f"Retrieving the data for {url} failed with failCode: {json_data[ATTR_FAIL_CODE]}, message: {json_data[ATTR_DATA]}"
                )

            if ATTR_DATA not in json_data:
                raise ZenchargerApiError(
                    f"Retrieving the data failed. Raw response: {response.text}"
                )

            return json_data

        except KeyError as error:
            _LOGGER.error(error)
            _LOGGER.error(response.text)


class ZenchargerApiError(Exception):
    """Generic Zencharger Api error."""


class ZenchargerApiAccessFrequencyTooHighError(ZenchargerApiError):
    pass


class ZenchargerApiErrorInvalidAccessToCurrentInterfaceError(ZenchargerApiError):
    pass

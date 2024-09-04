"""API client for Stroohm Dashboard."""

import logging

import httpx
from requests import get

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import ATTR_DATA, ATTR_FAIL_CODE
from .stroohm_websocket import StroohmWebSocket

_LOGGER = logging.getLogger(__name__)


class StroohmApi:
    """Api class."""

    @property
    def websocket(self):
        return self._websocket

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self._sessionId = None
        self._host = entry.data["credentials"]["host"]
        self._password = entry.data["credentials"]["password"]
        self._websocket = StroohmWebSocket(hass, entry)

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

            raise StroohmApiError("Could not login with given credentials")
        except Exception as error:
            raise StroohmApiError("Could not login with given credentials")

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

            raise StroohmApiError("Could not get status")
        except Exception as error:
            raise StroohmApiError("Could not get status")

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
                raise StroohmApiError(
                    f"Retrieving the data for {url} failed with failCode: {json_data[ATTR_FAIL_CODE]}, message: {json_data[ATTR_DATA]}"
                )

            if ATTR_DATA not in json_data:
                raise StroohmApiError(
                    f"Retrieving the data failed. Raw response: {response.text}"
                )

            return json_data

        except KeyError as error:
            _LOGGER.error(error)
            _LOGGER.error(response.text)


class StroohmApiError(Exception):
    """Generic Stroohm Api error."""


class StroohmApiAccessFrequencyTooHighError(StroohmApiError):
    pass


class StroohmApiErrorInvalidAccessToCurrentInterfaceError(StroohmApiError):
    pass

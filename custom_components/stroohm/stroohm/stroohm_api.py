"""API client for Stroohm Dashboard."""

import logging

import httpx
from requests import get

from .const import ATTR_DATA, ATTR_FAIL_CODE
from .stroohm_websocket import StroohmWebSocket

_LOGGER = logging.getLogger(__name__)


class StroohmApi:
    """Api class."""

    def __init__(self, host: str, password: str):
        self._sessionId = None
        self._host = host
        self._password = password
        self.websocket = StroohmWebSocket(host)

    async def ws_connect(self):
        if self._sessionId is None:
            self.login()
        await self.websocket.ws_connect(self._sessionId)

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
            _LOGGER.log(f"JSON data for {url}: {json_data}")

            # Session Expired code?
            if ATTR_FAIL_CODE in json_data and json_data[ATTR_FAIL_CODE] == 305:
                _LOGGER.log("Token expired, trying to login again")
                # token expired
                self._sessionId = None
                return self._do_call(url, body)

            if ATTR_FAIL_CODE in json_data and json_data[ATTR_FAIL_CODE] != 0:
                _LOGGER.log(
                    f"Error calling {url}: {json_data[ATTR_DATA]}, failcode: {json_data[ATTR_FAIL_CODE]}"
                )
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

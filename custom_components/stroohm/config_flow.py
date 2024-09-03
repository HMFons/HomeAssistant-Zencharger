"""Stroohm Api to call."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .const import CONF_CREDENTIALS, DOMAIN
from .stroohm.stroohm_api import StroohmApi, StroohmApiError

_LOGGER = logging.getLogger(__name__)


class StroohmConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config Flow of Stroohm Integration."""

    data: dict[str, Any] | None = {CONF_CREDENTIALS: {}}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Is invoked when a user initiates a flow via the user interface."""

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                api = StroohmApi(
                    user_input[CONF_HOST],
                    user_input[CONF_PASSWORD],
                )
                _ = await self.hass.async_add_executor_job(api.login)

                self.data[CONF_CREDENTIALS] = {
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PASSWORD: user_input[CONF_PASSWORD],
                }

                return self.async_create_entry(
                    title="Stroohm",
                    data=self.data,
                )

            except StroohmApiError as error:
                _LOGGER.log(error)
                errors["base"] = "invalid_credentials"

        return self.async_show_form(
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default="http://192.168.0.233"): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

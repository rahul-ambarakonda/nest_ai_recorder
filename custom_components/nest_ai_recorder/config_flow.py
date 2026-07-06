from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback

from .const import (
    CONF_CAMERA_NAME,
    CONF_MQTT_TOPIC_PREFIX,
    CONF_RTSP_URL,
    DEFAULT_CAMERA_NAME,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)


class NestAiRecorderConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, object] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(str(user_input[CONF_CAMERA_NAME]))
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=str(user_input[CONF_NAME]),
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default="Nest AI Recorder"): str,
                    vol.Required(CONF_CAMERA_NAME, default=DEFAULT_CAMERA_NAME): str,
                    vol.Required(CONF_RTSP_URL): str,
                    vol.Required(
                        CONF_MQTT_TOPIC_PREFIX,
                        default=DEFAULT_TOPIC_PREFIX,
                    ): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NestAiRecorderOptionsFlow(config_entry)


class NestAiRecorderOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, object] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MQTT_TOPIC_PREFIX,
                        default=self.config_entry.options.get(
                            CONF_MQTT_TOPIC_PREFIX,
                            self.config_entry.data.get(
                                CONF_MQTT_TOPIC_PREFIX,
                                DEFAULT_TOPIC_PREFIX,
                            ),
                        ),
                    ): str,
                }
            ),
        )


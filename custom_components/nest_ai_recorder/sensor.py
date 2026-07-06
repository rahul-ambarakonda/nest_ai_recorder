from __future__ import annotations

import json
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CAMERA_NAME,
    CONF_MQTT_TOPIC_PREFIX,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    camera_name = str(entry.data[CONF_CAMERA_NAME])
    async_add_entities([NestAiRecorderLastEventSensor(entry, camera_name)])


class NestAiRecorderLastEventSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Last Event"

    def __init__(self, entry: ConfigEntry, camera_name: str) -> None:
        self._entry = entry
        self._camera_name = camera_name
        self._attr_unique_id = f"{entry.entry_id}_last_event"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Nest AI Recorder {camera_name}",
            "manufacturer": "Nest AI Recorder",
        }
        self._native_value = "unknown"
        self._attr_extra_state_attributes: dict[str, Any] = {}

    @property
    def native_value(self) -> str:
        return self._native_value

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        topic_prefix = str(
            self._entry.options.get(
                CONF_MQTT_TOPIC_PREFIX,
                self._entry.data.get(CONF_MQTT_TOPIC_PREFIX, DEFAULT_TOPIC_PREFIX),
            )
        )
        topic = f"{topic_prefix}/{self._camera_name}/event"
        await mqtt.async_subscribe(self.hass, topic, self._message_received)
        _LOGGER.debug("Subscribed to MQTT topic %s", topic)

    @callback
    def _message_received(self, msg: mqtt.ReceiveMessage) -> None:
        try:
            payload = json.loads(msg.payload)
        except json.JSONDecodeError:
            _LOGGER.warning("Invalid MQTT payload on %s", msg.topic)
            return

        self._native_value = str(payload.get("type", "unknown"))
        self._attr_extra_state_attributes = {
            key: value for key, value in payload.items() if key != "type"
        }
        self.async_write_ha_state()

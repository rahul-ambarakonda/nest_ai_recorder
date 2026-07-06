from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_CAMERA_NAME, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    camera_name = str(entry.data[CONF_CAMERA_NAME])
    async_add_entities([NestAiRecorderLastEventSensor(entry.entry_id, camera_name)])


class NestAiRecorderLastEventSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Last Event"

    def __init__(self, entry_id: str, camera_name: str) -> None:
        self._attr_unique_id = f"{entry_id}_last_event"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": f"Nest AI Recorder {camera_name}",
            "manufacturer": "Nest AI Recorder",
        }
        self._native_value = "unknown"

    @property
    def native_value(self) -> str:
        return self._native_value


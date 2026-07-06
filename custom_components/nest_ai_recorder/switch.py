from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
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
    async_add_entities([NestAiRecorderRecordingSwitch(entry.entry_id, camera_name)])


class NestAiRecorderRecordingSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Recording"

    def __init__(self, entry_id: str, camera_name: str) -> None:
        self._attr_unique_id = f"{entry_id}_recording"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry_id)},
            "name": f"Nest AI Recorder {camera_name}",
            "manufacturer": "Nest AI Recorder",
        }
        self._is_on = True

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._is_on = False
        self.async_write_ha_state()


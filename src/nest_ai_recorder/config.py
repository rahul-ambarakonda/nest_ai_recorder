from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, PositiveInt, field_validator


class CameraConfig(BaseModel):
    name: str = "front_door"
    rtsp_url: str


class BufferConfig(BaseModel):
    directory: Path = Path("/media/nest-ai-recorder/buffer")
    duration_seconds: PositiveInt = 120
    segment_seconds: PositiveInt = 10

    @field_validator("duration_seconds")
    @classmethod
    def duration_must_cover_multiple_segments(cls, value: int) -> int:
        if value < 10:
            raise ValueError("buffer duration must be at least 10 seconds")
        return value


class ClipConfig(BaseModel):
    output_directory: Path = Path("/media/videos")
    pre_buffer_seconds: PositiveInt = 10
    post_buffer_seconds: PositiveInt = 50
    retention_days: PositiveInt = 30


class DetectionConfig(BaseModel):
    enabled: bool = False
    confidence: float = Field(default=0.55, ge=0.0, le=1.0)
    object_classes: list[str] = Field(default_factory=lambda: ["person"])
    ignore_motion_without_object: bool = True
    cooldown_seconds: PositiveInt = 90
    ignore_zones: list[list[tuple[int, int]]] = Field(default_factory=list)
    detection_zones: list[list[tuple[int, int]]] = Field(default_factory=list)


class MqttConfig(BaseModel):
    enabled: bool = False
    host: str = "core-mosquitto"
    port: PositiveInt = 1883
    username: str = ""
    password: str = ""
    topic_prefix: str = "nest_ai_recorder"


class LoggingConfig(BaseModel):
    directory: Path = Path("/logs")
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    max_bytes: PositiveInt = 10_485_760
    backup_count: PositiveInt = 5


class AppConfig(BaseModel):
    camera: CameraConfig
    buffer: BufferConfig = Field(default_factory=BufferConfig)
    clips: ClipConfig = Field(default_factory=ClipConfig)
    detection: DetectionConfig = Field(default_factory=DetectionConfig)
    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @field_validator("buffer")
    @classmethod
    def buffer_must_fit_segment_grid(cls, value: BufferConfig) -> BufferConfig:
        if value.duration_seconds % value.segment_seconds != 0:
            raise ValueError("buffer duration must be divisible by segment length")
        return value


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    return AppConfig.model_validate(raw)



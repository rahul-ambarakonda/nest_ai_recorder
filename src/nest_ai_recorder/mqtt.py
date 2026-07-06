from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import timezone
from pathlib import Path

from nest_ai_recorder.config import MqttConfig
from nest_ai_recorder.events import DetectionEvent


@dataclass(frozen=True, slots=True)
class MqttPayload:
    topic: str
    body: dict[str, object]


def event_payload(
    event: DetectionEvent,
    clip_path: Path | None,
    topic_prefix: str,
) -> MqttPayload:
    timestamp = event.timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    body: dict[str, object] = {
        "type": event.event_type,
        "camera": event.camera,
        "timestamp": timestamp,
        "confidence": event.confidence,
    }
    if clip_path is not None:
        body["clip"] = str(clip_path)
    if event.track_id is not None:
        body["track_id"] = event.track_id
    return MqttPayload(
        topic=f"{topic_prefix}/{event.camera}/event",
        body=body,
    )


class MqttPublisher:
    def __init__(self, config: MqttConfig) -> None:
        self.config = config
        self._client = None

    def connect(self) -> None:
        if not self.config.enabled:
            return
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise RuntimeError("paho-mqtt is not installed. Install nest-ai-recorder[mqtt].") from exc

        client = mqtt.Client()
        if self.config.username:
            client.username_pw_set(self.config.username, self.config.password)
        client.connect(self.config.host, self.config.port)
        client.loop_start()
        self._client = client

    def publish(self, payload: MqttPayload) -> None:
        if self._client is None:
            return
        self._client.publish(payload.topic, json.dumps(payload.body), retain=False)

    def close(self) -> None:
        if self._client is None:
            return
        self._client.loop_stop()
        self._client.disconnect()
        self._client = None


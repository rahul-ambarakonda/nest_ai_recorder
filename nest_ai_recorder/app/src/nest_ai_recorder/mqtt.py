from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from datetime import timezone
from pathlib import Path

from nest_ai_recorder.config import MqttConfig
from nest_ai_recorder.events import DetectionEvent

LOGGER = logging.getLogger(__name__)

MQTT_RC_MESSAGES = {
    1: "incorrect protocol version",
    2: "invalid client identifier",
    3: "broker unavailable",
    4: "bad username or password",
    5: "not authorised",
}


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

        if not self.config.username:
            LOGGER.warning(
                "mqtt username is empty; Mosquitto on Home Assistant usually requires authentication"
            )

        connected = threading.Event()
        result_code: list[int | None] = [None]

        def on_connect(client, userdata, flags, rc, properties=None) -> None:
            result_code[0] = rc
            connected.set()

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        client.on_connect = on_connect
        if self.config.username:
            client.username_pw_set(self.config.username, self.config.password)

        client.connect(self.config.host, self.config.port)
        client.loop_start()

        if not connected.wait(timeout=5):
            client.loop_stop()
            raise RuntimeError(
                f"timed out connecting to mqtt broker at {self.config.host}:{self.config.port}"
            )

        rc = result_code[0]
        if rc != 0:
            client.loop_stop()
            reason = MQTT_RC_MESSAGES.get(rc, f"error code {rc}")
            raise RuntimeError(
                "mqtt authentication failed: "
                f"{reason}. Add mqtt.username and mqtt.password to /config/nest_ai_recorder.yaml"
            )

        self._client = client
        LOGGER.info(
            "connected to mqtt broker",
            extra={
                "host": self.config.host,
                "port": self.config.port,
                "username": self.config.username or "(none)",
            },
        )

    def publish(self, payload: MqttPayload) -> None:
        if self._client is None:
            LOGGER.warning("skipped mqtt publish because client is not connected")
            return
        result = self._client.publish(payload.topic, json.dumps(payload.body), retain=False)
        if result.rc != 0:
            LOGGER.warning(
                "mqtt publish failed",
                extra={"topic": payload.topic, "rc": result.rc},
            )
            return
        LOGGER.info("published mqtt event", extra={"topic": payload.topic, "type": payload.body.get("type")})

    def close(self) -> None:
        if self._client is None:
            return
        self._client.loop_stop()
        self._client.disconnect()
        self._client = None

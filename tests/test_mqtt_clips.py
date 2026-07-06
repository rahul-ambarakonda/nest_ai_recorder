from datetime import datetime, timezone
from pathlib import Path

import pytest

from nest_ai_recorder.clips import build_ffmpeg_concat_command
from nest_ai_recorder.events import DetectionEvent
from nest_ai_recorder.mqtt import event_payload


def test_build_ffmpeg_concat_command_requires_segments() -> None:
    with pytest.raises(ValueError, match="at least one segment"):
        build_ffmpeg_concat_command([], Path("out.mp4"))


def test_build_ffmpeg_concat_command_contains_placeholder() -> None:
    command = build_ffmpeg_concat_command([Path("a.mp4")], Path("out.mp4"))

    assert command[:2] == ["ffmpeg", "-hide_banner"]
    assert "{concat_file}" in command
    assert command[-1] == "out.mp4"


def test_mqtt_event_payload_includes_clip_and_track() -> None:
    event = DetectionEvent(
        event_type="person",
        camera="front_door",
        timestamp=datetime(2026, 7, 6, 8, 30, tzinfo=timezone.utc),
        confidence=0.82,
        track_id="1",
    )

    payload = event_payload(event, Path("/media/person.mp4"), "nest_ai_recorder")

    assert payload.topic == "nest_ai_recorder/front_door/event"
    assert payload.body["timestamp"] == "2026-07-06T08:30:00Z"
    assert payload.body["clip"] == "\\media\\person.mp4" or payload.body["clip"] == "/media/person.mp4"
    assert payload.body["track_id"] == "1"

from datetime import datetime, timezone
from pathlib import Path

import pytest

import nest_ai_recorder.pipeline as pipeline_module
from nest_ai_recorder.config import AppConfig, CameraConfig
from nest_ai_recorder.detection import Detection
from nest_ai_recorder.geometry import Box
from nest_ai_recorder.pipeline import EventPipeline
from nest_ai_recorder.segments import Segment
from nest_ai_recorder.stats import StatsStore


@pytest.mark.asyncio
async def test_event_pipeline_creates_clip_and_updates_stats(monkeypatch, tmp_path: Path) -> None:
    async def fake_merge(segment_paths, output_path, timeout_seconds=120):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("clip", encoding="utf-8")
        return output_path

    monkeypatch.setattr(pipeline_module, "merge_segments", fake_merge)
    config = AppConfig(
        camera=CameraConfig(name="front_door", rtsp_url="rtsp://example.local/front"),
    )
    config.clips.output_directory = tmp_path / "videos"
    stats = StatsStore(tmp_path / "stats.json")
    event_pipeline = EventPipeline(config, stats=stats)
    timestamp = datetime(2026, 7, 6, 8, 30, tzinfo=timezone.utc)
    segments = [
        Segment(tmp_path / "a.mp4", datetime(2026, 7, 6, 8, 29, 50, tzinfo=timezone.utc), 10),
        Segment(tmp_path / "b.mp4", datetime(2026, 7, 6, 8, 30, 0, tzinfo=timezone.utc), 10),
    ]
    detection = Detection("person", 0.9, Box(0, 0, 100, 100), track_id="1")

    clip_path = await event_pipeline.handle_detection(detection, timestamp, segments)

    assert clip_path is not None
    assert clip_path.exists()
    assert stats.stats.events_total == 1
    assert stats.stats.clips_total == 1


@pytest.mark.asyncio
async def test_event_pipeline_deduplicates(monkeypatch, tmp_path: Path) -> None:
    calls = 0

    async def fake_merge(segment_paths, output_path, timeout_seconds=120):
        nonlocal calls
        calls += 1
        return output_path

    monkeypatch.setattr(pipeline_module, "merge_segments", fake_merge)
    config = AppConfig(
        camera=CameraConfig(name="front_door", rtsp_url="rtsp://example.local/front"),
    )
    event_pipeline = EventPipeline(config)
    timestamp = datetime(2026, 7, 6, 8, 30, tzinfo=timezone.utc)
    segments = [Segment(tmp_path / "a.mp4", timestamp, 10)]
    detection = Detection("person", 0.9, Box(0, 0, 100, 100), track_id="1")

    first = await event_pipeline.handle_detection(detection, timestamp, segments)
    second = await event_pipeline.handle_detection(detection, timestamp, segments)

    assert first is not None
    assert second is None
    assert calls == 1

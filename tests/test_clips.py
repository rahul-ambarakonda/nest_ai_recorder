from datetime import datetime, timezone
from pathlib import Path

from nest_ai_recorder.clips import clip_output_path, plan_clip_segments
from nest_ai_recorder.segments import Segment


def test_clip_output_path_uses_spec_directory_layout() -> None:
    event_time = datetime(2026, 7, 6, 8, 30, 0, tzinfo=timezone.utc)

    path = clip_output_path(Path("/media/videos"), "person", event_time)

    assert path == Path("/media/videos/07-2026/06-07-2026/person_20260706_083000.mp4")


def test_plan_clip_segments_returns_paths_only() -> None:
    event_time = datetime(2026, 7, 6, 8, 30, 0, tzinfo=timezone.utc)
    segments = [
        Segment(Path("before.mp4"), datetime(2026, 7, 6, 8, 29, 50, tzinfo=timezone.utc), 10),
        Segment(Path("after.mp4"), datetime(2026, 7, 6, 8, 30, 0, tzinfo=timezone.utc), 10),
    ]

    assert plan_clip_segments(segments, event_time, 10, 10) == [
        Path("before.mp4"),
        Path("after.mp4"),
    ]


# API Notes

The internal Python API is organized around small, testable modules:

- `nest_ai_recorder.config.load_config(path)` validates YAML configuration.
- `nest_ai_recorder.segments.discover_segments(path, segment_seconds)` finds
  valid MP4 segments.
- `nest_ai_recorder.segments.select_segments(...)` chooses the segments that
  overlap an event window.
- `nest_ai_recorder.events.EventDeduplicator` suppresses repeated events during
  the configured cooldown.
- `nest_ai_recorder.recorder.SegmentRecorder` runs ffmpeg against the RTSP URL.

Public HTTP APIs are planned for a later dashboard phase.


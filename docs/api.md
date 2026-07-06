# API Notes

The internal Python API is organized around small, testable modules:

- `nest_ai_recorder.config.load_config(path)` validates YAML configuration.
- `nest_ai_recorder.segments.discover_segments(path, segment_seconds)` finds
  valid MP4 segments.
- `nest_ai_recorder.segments.select_segments(...)` chooses the segments that
  overlap an event window.
- `nest_ai_recorder.detection.ZoneFilter` applies ignore and detection zones.
- `nest_ai_recorder.detection.IouTracker` provides lightweight track IDs.
- `nest_ai_recorder.events.EventDeduplicator` suppresses repeated events during
  the configured cooldown.
- `nest_ai_recorder.clips.merge_segments(...)` exports clips through ffmpeg
  concat demuxer.
- `nest_ai_recorder.mqtt.event_payload(...)` creates Home Assistant-friendly
  MQTT JSON payloads.
- `nest_ai_recorder.service.RecorderService` composes recorder, detection,
  MQTT, stats, and dashboard pieces.

The dashboard exposes `GET /api/stats` for JSON statistics.

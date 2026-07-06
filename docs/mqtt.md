# MQTT Payloads

The planned event topic is:

```text
nest_ai_recorder/front_door/event
```

Example payload:

```json
{
  "type": "person",
  "camera": "front_door",
  "timestamp": "2026-07-06T08:30:00Z",
  "confidence": 0.82,
  "clip": "/media/videos/07-2026/06-07-2026/person_20260706_083000.mp4"
}
```

MQTT publishing is planned for Phase 4, after detection and clip export are
fully wired.


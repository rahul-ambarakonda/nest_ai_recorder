# Troubleshooting

## No segments are created

- Confirm the go2rtc RTSP URL opens from the same machine or container network.
- Confirm ffmpeg is installed in the runtime environment.
- Check `/logs/nest-ai-recorder.log`.

## Segments are created but clips are incomplete

- Increase `buffer.duration_seconds`.
- Confirm `buffer.duration_seconds` is divisible by `buffer.segment_seconds`.
- Make sure the camera stream has stable timestamps.

## Home Assistant entities do not appear

- Restart Home Assistant after copying `custom_components/nest_ai_recorder`.
- Add the integration from Settings > Devices & services.
- Check Home Assistant logs for config flow or dependency errors.


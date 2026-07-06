# Troubleshooting

## HACS download failed (404 zipball)

HACS may fail with an error like:

```text
Got status code 404 when trying to download .../archive/refs/heads/28209cb.zip
```

HACS is trying to download a commit hash as if it were a branch name. Do not use
HACS for now. Install manually instead:

1. In HACS, remove **Nest AI Recorder** if it is listed.
2. Delete the broken folder: `/config/custom_components/nest_ai_recorder/`
3. Download the latest release ZIP from GitHub:
   `https://github.com/rahul-ambarakonda/nest_ai_recorder/releases/latest`
4. Copy only the `custom_components/nest_ai_recorder/` folder into
   `/config/custom_components/nest_ai_recorder/`
5. Confirm `manifest.json` shows `"version": "0.1.3"`.
6. Restart Home Assistant.

## Setup failed for dependencies: mqtt

The integration requires Home Assistant's **MQTT** integration.

1. Install the **Mosquitto broker** add-on (if you do not already have a broker).
2. Go to **Settings → Devices & services → Add integration → MQTT**.
3. Complete MQTT setup.
4. Restart Home Assistant.
5. Add **Nest AI Recorder** again.

## Add-on image build failed

The add-on avoids YOLO on Raspberry Pi because Ultralytics/PyTorch does not
build reliably on Alpine aarch64. The add-on uses motion-based detection
instead.

1. Update the add-on repository in **Settings → Add-ons → Add-on store → Check
   for updates**.
2. Uninstall the failed add-on if needed, then install **Nest AI Recorder**
   again.
3. If install still fails, open **Settings → System → Logs → Supervisor** and
   search for `nest_ai_recorder`.
4. Confirm `/config/nest_ai_recorder.yaml` includes:

```yaml
detection:
  enabled: true
  ignore_motion_without_object: false
  motion_min_score: 0.01
  cooldown_seconds: 30
```

Events will publish as `"type": "motion"` over MQTT when movement is detected.

## No events appear

The custom integration does not run detection by itself. You must also install
and start the **Nest AI Recorder add-on** (or a systemd service on the host).

Check each layer in order:

1. **Add-on is installed and running**
   - **Settings → Add-ons → Nest AI Recorder → Start**
   - Open the add-on **Log** tab and confirm there are no errors about OpenCV,
     RTSP, or MQTT.
2. **Config file path is correct**
   - Use `/config/nest_ai_recorder.yaml` (File editor may show this as
     `/homeassistant/nest_ai_recorder.yaml`).
3. **Recorder MQTT is enabled** in `/config/nest_ai_recorder.yaml`:

```yaml
mqtt:
  enabled: true
  host: 127.0.0.1
  port: 1883
  topic_prefix: nest_ai_recorder
```

Use `127.0.0.1` when the add-on runs with host networking. Use
`core-mosquitto` only for non-host-network setups.

4. **Detection is enabled** with motion settings on Raspberry Pi.
5. **Camera name matches** between recorder config and the HA integration
   (`camera.name` and **Camera name** in the config flow).
6. **Listen for MQTT messages** in **Developer tools → MQTT** on topic:
   `nest_ai_recorder/front_door/event`
7. **go2rtc stream name matches** the stream URL. If go2rtc shows `nest_doorbell`,
   prefer the HTTP URL:
   `http://127.0.0.1:1984/api/stream.mp4?src=nest_doorbell`
   RTSP can show `non-existing PPS 0 referenced` errors with Nest/go2rtc.

## nest_doorbell_record shows 404 or exec/rtsp errors

If go2rtc logs show:

```text
404 Not Found rtsp://127.0.0.1:8554/nest_doorbell_record
exec/rtsp Output file does not contain any stream
```

The ffmpeg restream was configured incorrectly.

Fix it:

1. Open `/config/go2rtc.yaml`
2. Remove any broken `nest_doorbell_record` block
3. Add it back with **one line only**:

```yaml
streams:
  nest_doorbell:
    - ... keep your existing nest source ...

  nest_doorbell_record:
    - ffmpeg:nest_doorbell#video=h264
```

4. Do **not** use `rtsp://127.0.0.1:8554/nest_doorbell` inside
   `nest_doorbell_record`
5. Restart the **go2rtc** add-on
6. In go2rtc UI, confirm `nest_doorbell_record` shows **online** and preview works
7. Only then set recorder config to:

```yaml
camera:
  rtsp_url: rtsp://127.0.0.1:8554/nest_doorbell_record
```

Until the restream works, use the original stream instead:

```yaml
camera:
  rtsp_url: rtsp://127.0.0.1:8554/nest_doorbell
```

See `config/go2rtc.example.yaml` for a full example.

## H264 PPS / corrupt frame errors in add-on log

If the log shows repeated messages like:

```text
non-existing PPS 0 referenced
decode_slice_header error
corrupt decoded frame
```

Switch from RTSP to the go2rtc HTTP stream in `/config/nest_ai_recorder.yaml`:

```yaml
camera:
  rtsp_url: http://127.0.0.1:1984/api/stream.mp4?src=nest_doorbell
```

On Home Assistant OS, port `1984` is often **not exposed on localhost**. Prefer RTSP
on port `8554` and use buffer-based motion detection:

```yaml
camera:
  rtsp_url: rtsp://127.0.0.1:8554/nest_doorbell

detection:
  enabled: true
  frame_source: buffer
```

This uses one live stream for recording and reads completed buffer files for motion
events, which avoids overloading the Nest/go2rtc stream.

## Home Assistant entities do not appear

- Restart Home Assistant after copying `custom_components/nest_ai_recorder`.
- Add the integration from **Settings → Devices & services**.
- Check Home Assistant logs for config flow or dependency errors.
- Confirm `manifest.json` is valid JSON and not an empty file.

## No segments are created

- Confirm the go2rtc RTSP URL opens from the same machine or container network.
- Confirm ffmpeg is installed in the runtime environment.
- Check `/logs/nest-ai-recorder.log`.

## Segments are created but clips are incomplete

- Increase `buffer.duration_seconds`.
- Confirm `buffer.duration_seconds` is divisible by `buffer.segment_seconds`.
- Make sure the camera stream has stable timestamps.

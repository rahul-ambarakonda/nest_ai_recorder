# Troubleshooting

## HACS download failed (404 zipball)

HACS may fail with an error like:

```text
Got status code 404 when trying to download .../archive/refs/heads/88e9bea.zip
```

That leaves an empty `manifest.json` and breaks the integration. Fix it with a
manual install:

1. In HACS, remove **Nest AI Recorder** if it is listed.
2. Delete the broken folder: `/config/custom_components/nest_ai_recorder/`
3. Download the repo as ZIP from GitHub:
   `https://github.com/rahul-ambarakonda/nest_ai_recorder/archive/refs/heads/main.zip`
4. Copy only the `custom_components/nest_ai_recorder/` folder into
   `/config/custom_components/nest_ai_recorder/`
5. Confirm `manifest.json` is not empty.
6. Restart Home Assistant.

## Setup failed for dependencies: mqtt

The integration requires Home Assistant's **MQTT** integration.

1. Install the **Mosquitto broker** add-on (if you do not already have a broker).
2. Go to **Settings → Devices & services → Add integration → MQTT**.
3. Complete MQTT setup.
4. Restart Home Assistant.
5. Add **Nest AI Recorder** again.

## No events appear

The custom integration does not run detection by itself. You must also install
and start the **Nest AI Recorder add-on** (or a systemd service on the host).

Check each layer in order:

1. **Add-on is installed and running**
   - **Settings → Add-ons → Nest AI Recorder → Start**
   - Open the add-on **Log** tab and confirm there are no errors about OpenCV,
     Ultralytics, RTSP, or MQTT.
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

4. **Detection is enabled** and AI packages are installed in the add-on image.
5. **Camera name matches** between recorder config and the HA integration
   (`camera.name` and **Camera name** in the config flow).
6. **Listen for MQTT messages** in **Developer tools → MQTT** on topic:
   `nest_ai_recorder/front_door/event`
7. **go2rtc stream name matches** the RTSP URL. If go2rtc shows `nest_doorbell`,
   the URL must be `rtsp://127.0.0.1:8554/nest_doorbell`.
8. **First model download** can take a few minutes after the add-on starts.

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

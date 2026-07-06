# Installation

You do not need Docker to run Nest AI Recorder on a Raspberry Pi with Home
Assistant. Use the Home Assistant OS add-on (recommended) or install the Python
package directly on the host.

## Home Assistant OS Add-on (Recommended)

The add-on runs the recorder as a managed Home Assistant service with access to
go2rtc, MQTT, and the `/media` folder.

1. Add this repository as a custom add-on repository in Home Assistant
   (**Settings → Add-ons → Add-on store → ⋮ → Repositories**).
2. Install the **Nest AI Recorder** add-on.
3. Copy `config/config.example.yaml` to `/config/nest_ai_recorder.yaml` on your
   Home Assistant config volume.
4. Set `camera.rtsp_url` to your go2rtc RTSP stream, for example:
   `rtsp://127.0.0.1:8554/nest_front_door`
5. Enable MQTT and point it at the Mosquitto broker:

```yaml
mqtt:
  enabled: true
  host: core-mosquitto
  port: 1883
  topic_prefix: nest_ai_recorder
```

6. Start the add-on.

The dashboard is available on port `8099` when `dashboard.enabled` is true.

## Direct Install on Raspberry Pi

If you run Home Assistant Container or want the recorder outside the add-on
system, install the Python package on the Pi host.

1. Install system dependencies:

```bash
sudo apt update
sudo apt install -y ffmpeg python3 python3-pip python3-venv
```

2. Create a virtual environment and install the package:

```bash
python3 -m venv /opt/nest-ai-recorder/venv
/opt/nest-ai-recorder/venv/bin/pip install "nest-ai-recorder[mqtt]"
```

For local YOLO detection, also install the AI extra:

```bash
/opt/nest-ai-recorder/venv/bin/pip install "nest-ai-recorder[mqtt,ai]"
```

3. Copy `config/config.example.yaml` to `/config/nest_ai_recorder.yaml` (or
   another path) and edit the RTSP URL, media paths, and MQTT settings.
4. Validate the config:

```bash
/opt/nest-ai-recorder/venv/bin/nest-ai-recorder --config /config/nest_ai_recorder.yaml check-config
```

5. Create a systemd service at `/etc/systemd/system/nest-ai-recorder.service`:

```ini
[Unit]
Description=Nest AI Recorder
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=homeassistant
Group=homeassistant
Environment=NEST_AI_RECORDER_CONFIG=/config/nest_ai_recorder.yaml
ExecStart=/opt/nest-ai-recorder/venv/bin/nest-ai-recorder serve
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

6. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nest-ai-recorder
```

## AI Runtime

Set `detection.enabled: true` only after installing the `ai` extra:

```text
nest-ai-recorder[ai]
```

Keep `detection.enabled: false` until the model packages are installed.

## Home Assistant Custom Integration

Copy `custom_components/nest_ai_recorder` into Home Assistant's
`custom_components` directory, restart Home Assistant, then add the integration
from **Settings → Devices & services**.

The custom integration is the UI and entity layer. The recorder process runs as
the Home Assistant add-on or as the systemd service above.

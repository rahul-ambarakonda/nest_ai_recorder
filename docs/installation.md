# Installation

## Docker

1. Copy `config/config.example.yaml` to `config/config.yaml`.
2. Set `camera.rtsp_url` to the go2rtc RTSP stream for the Nest camera.
3. Start the service:

```powershell
docker compose up --build
```

The dashboard is available on port `8099` when `dashboard.enabled` is true.

## AI Runtime

For local YOLO detection, install the AI extra in the runtime image or extend the
Dockerfile to include:

```text
nest-ai-recorder[ai]
```

Keep `detection.enabled: false` until the model packages are installed.

## Home Assistant Custom Integration

Copy `custom_components/nest_ai_recorder` into Home Assistant's
`custom_components` directory, restart Home Assistant, then add the integration
from Settings > Devices & services.

The custom integration is the UI and entity layer. The recorder process still
runs as a Docker container or Home Assistant add-on.

## Home Assistant OS Add-on

The `addon` directory contains the add-on scaffold. It runs the same
`nest-ai-recorder serve` command as the Docker image.

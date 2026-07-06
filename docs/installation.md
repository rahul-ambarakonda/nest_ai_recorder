# Installation

## Docker

1. Copy `config/config.example.yaml` to `config/config.yaml`.
2. Set `camera.rtsp_url` to the go2rtc RTSP stream for the Nest camera.
3. Start the service:

```powershell
docker compose up --build
```

## Home Assistant Custom Integration

Copy `custom_components/nest_ai_recorder` into Home Assistant's
`custom_components` directory, restart Home Assistant, then add the integration
from Settings > Devices & services.

The custom integration is the UI and entity layer. The recorder process still
runs as a Docker container or Home Assistant add-on.

## Home Assistant OS Add-on

The `addon` directory contains the add-on scaffold. Phase 1 keeps the add-on
metadata in place while the runtime image is developed from the root Dockerfile.


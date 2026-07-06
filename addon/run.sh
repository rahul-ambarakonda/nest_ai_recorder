#!/usr/bin/with-contenv sh
set -eu

CONFIG_PATH="$(jq -r '.config_path' /data/options.json)"
exec nest-ai-recorder --config "$CONFIG_PATH" run


from pathlib import Path

import pytest
import yaml

from nest_ai_recorder.config import load_config


def test_load_config_validates_segment_grid(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "camera": {
                    "name": "front_door",
                    "rtsp_url": "rtsp://example.local:8554/front_door",
                },
                "buffer": {
                    "duration_seconds": 125,
                    "segment_seconds": 10,
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="divisible"):
        load_config(config_path)


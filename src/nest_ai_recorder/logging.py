from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from pythonjsonlogger import jsonlogger

from nest_ai_recorder.config import LoggingConfig


def configure_logging(config: LoggingConfig) -> None:
    config.directory.mkdir(parents=True, exist_ok=True)
    log_file = config.directory / "nest-ai-recorder.log"

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(config.level)

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)



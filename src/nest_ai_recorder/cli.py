from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from nest_ai_recorder.config import load_config
from nest_ai_recorder.logging import configure_logging
from nest_ai_recorder.recorder import SegmentRecorder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nest-ai-recorder")
    parser.add_argument(
        "--config",
        default=os.environ.get("NEST_AI_RECORDER_CONFIG", "config/config.yaml"),
        help="Path to recorder YAML configuration.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run", help="Run the continuous segment recorder.")
    subparsers.add_parser("check-config", help="Validate configuration and exit.")
    return parser


async def run_recorder(config_path: Path) -> int:
    config = load_config(config_path)
    configure_logging(config.logging)
    recorder = SegmentRecorder(config)
    return await recorder.run()


def main() -> None:
    args = build_parser().parse_args()
    config_path = Path(args.config)

    if args.command == "check-config":
        load_config(config_path)
        return

    if args.command == "run":
        raise SystemExit(asyncio.run(run_recorder(config_path)))


#!/usr/bin/env python3
"""Music provider adapter for video jobs.

The public skill supports multiple music backends. This script starts with a
safe local contract and leaves provider-specific endpoints behind adapters so
API changes do not break the skill instructions.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def emit(payload):
    print("RESULT: " + json.dumps(payload), flush=True)


def validate_elevenlabs(args):
    load_dotenv()
    if not os.getenv("ELEVENLABS_API_KEY"):
        emit({"status": "failed", "provider": "elevenlabs", "error": "ELEVENLABS_API_KEY missing in .env"})
        sys.exit(2)
    emit({
        "status": "ready",
        "provider": "elevenlabs",
        "next_action": "Call your configured ElevenLabs music endpoint or SDK wrapper.",
        "prompt": args.prompt,
        "duration_seconds": args.duration,
    })


def use_existing(args):
    path = Path(args.path).expanduser().resolve()
    if not path.exists():
        emit({"status": "failed", "provider": "local", "error": f"Music file not found: {path}"})
        sys.exit(2)
    emit({
        "status": "succeeded",
        "provider": "local",
        "local_path": str(path),
        "next_action": "Mix this file under voiceover with FFmpeg.",
    })


def build_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    eleven = sub.add_parser("elevenlabs-plan")
    eleven.add_argument("--prompt", required=True)
    eleven.add_argument("--duration", type=int, default=30)
    eleven.set_defaults(func=validate_elevenlabs)

    local = sub.add_parser("local")
    local.add_argument("--path", required=True)
    local.set_defaults(func=use_existing)

    return parser


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

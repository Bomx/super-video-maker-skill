#!/usr/bin/env python3
"""OpenAI image generation/editing helper for video assets.

This is intentionally small: agents call this script instead of writing raw API
calls. It saves outputs locally and emits one RESULT JSON line.
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


DEFAULT_MODEL = "gpt-image-2"


def emit(payload):
    print("RESULT: " + json.dumps(payload), flush=True)


def output_dir():
    out = Path.cwd() / "output_images"
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_b64_image(b64_data, prefix="image"):
    path = output_dir() / f"{prefix}_{int(time.time())}.png"
    path.write_bytes(base64.b64decode(b64_data))
    return path


def generate(args):
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        emit({"status": "failed", "error": "OPENAI_API_KEY missing in .env", "provider": "openai"})
        sys.exit(2)

    client = OpenAI()
    try:
        print(f"[image_provider] Generating image with {args.model}: {args.prompt[:120]}", file=sys.stderr)
        result = client.images.generate(
            model=args.model,
            prompt=args.prompt,
            size=args.size,
        )
        item = result.data[0]
        b64_data = getattr(item, "b64_json", None)
        if not b64_data:
            emit({"status": "failed", "error": "No b64_json returned by image API", "provider": "openai"})
            sys.exit(1)
        path = save_b64_image(b64_data, "openai_image")
        emit({
            "status": "succeeded",
            "provider": "openai",
            "model": args.model,
            "prompt": args.prompt,
            "size": args.size,
            "local_path": str(path),
        })
    except Exception as exc:
        emit({"status": "failed", "error": str(exc), "provider": "openai", "model": args.model})
        sys.exit(1)


def build_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--prompt", required=True)
    gen.add_argument("--size", default="1024x1024")
    gen.add_argument("--model", default=DEFAULT_MODEL)
    gen.set_defaults(func=generate)
    return parser


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""OpenAI image generation/editing helper for video assets.

This is intentionally small: agents call this script instead of writing raw API
calls. It saves outputs locally and emits one RESULT JSON line.
"""

import argparse
import base64
from contextlib import ExitStack
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


def save_b64_image(b64_data, prefix="image", output_format="png"):
    ext = "jpg" if output_format == "jpeg" else output_format
    path = output_dir() / f"{prefix}_{int(time.time())}.{ext}"
    path.write_bytes(base64.b64decode(b64_data))
    return path


def require_openai_key():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        emit({"status": "failed", "error": "OPENAI_API_KEY missing in .env", "provider": "openai"})
        sys.exit(2)


def optional_kwargs(**kwargs):
    return {key: value for key, value in kwargs.items() if value is not None}


def first_image_b64(result):
    item = result.data[0]
    b64_data = getattr(item, "b64_json", None)
    if not b64_data:
        emit({"status": "failed", "error": "No b64_json returned by image API", "provider": "openai"})
        sys.exit(1)
    return b64_data


def generate(args):
    require_openai_key()
    client = OpenAI()
    try:
        print(f"[image_provider] Generating image with {args.model}: {args.prompt[:120]}", file=sys.stderr)
        result = client.images.generate(**optional_kwargs(
            model=args.model,
            prompt=args.prompt,
            size=args.size,
            quality=args.quality,
            background=args.background,
            output_format=args.output_format,
            output_compression=args.output_compression,
        ))
        b64_data = first_image_b64(result)
        path = save_b64_image(b64_data, "openai_image", args.output_format or "png")
        emit({
            "status": "succeeded",
            "provider": "openai",
            "model": args.model,
            "prompt": args.prompt,
            "size": args.size,
            "quality": args.quality,
            "output_format": args.output_format or "png",
            "local_path": str(path),
        })
    except Exception as exc:
        emit({"status": "failed", "error": str(exc), "provider": "openai", "model": args.model})
        sys.exit(1)


def edit(args):
    require_openai_key()
    client = OpenAI()
    try:
        with ExitStack() as stack:
            images = []
            for ref in args.reference_image:
                path = Path(ref).expanduser()
                if not path.exists():
                    emit({"status": "failed", "error": f"reference image not found: {ref}", "provider": "openai"})
                    sys.exit(2)
                images.append(stack.enter_context(path.open("rb")))

            mask = None
            if args.mask:
                mask_path = Path(args.mask).expanduser()
                if not mask_path.exists():
                    emit({"status": "failed", "error": f"mask not found: {args.mask}", "provider": "openai"})
                    sys.exit(2)
                mask = stack.enter_context(mask_path.open("rb"))

            print(
                f"[image_provider] Editing {len(images)} reference image(s) with {args.model}: "
                f"{args.prompt[:120]}",
                file=sys.stderr,
            )
            result = client.images.edit(**optional_kwargs(
                model=args.model,
                image=images if len(images) > 1 else images[0],
                mask=mask,
                prompt=args.prompt,
                size=args.size,
                quality=args.quality,
                background=args.background,
                input_fidelity=args.input_fidelity,
                output_format=args.output_format,
                output_compression=args.output_compression,
            ))

        b64_data = first_image_b64(result)
        path = save_b64_image(b64_data, "openai_edit", args.output_format or "png")
        emit({
            "status": "succeeded",
            "provider": "openai",
            "operation": "edit",
            "model": args.model,
            "prompt": args.prompt,
            "size": args.size,
            "quality": args.quality,
            "input_fidelity": args.input_fidelity,
            "reference_images": args.reference_image,
            "output_format": args.output_format or "png",
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
    gen.add_argument("--quality", default="high")
    gen.add_argument("--background", default=None)
    gen.add_argument("--output-format", default="png", choices=["png", "jpeg", "webp"])
    gen.add_argument("--output-compression", type=int, default=None)
    gen.set_defaults(func=generate)

    edit_cmd = sub.add_parser("edit")
    edit_cmd.add_argument("--reference-image", action="append", required=True, help="Local path. Repeat up to the provider limit.")
    edit_cmd.add_argument("--mask", default=None, help="Optional local mask path.")
    edit_cmd.add_argument("--prompt", required=True)
    edit_cmd.add_argument("--size", default="1024x1024")
    edit_cmd.add_argument("--model", default=DEFAULT_MODEL)
    edit_cmd.add_argument("--quality", default="high")
    edit_cmd.add_argument("--input-fidelity", default=None)
    edit_cmd.add_argument("--background", default=None)
    edit_cmd.add_argument("--output-format", default="png", choices=["png", "jpeg", "webp"])
    edit_cmd.add_argument("--output-compression", type=int, default=None)
    edit_cmd.set_defaults(func=edit)

    return parser


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

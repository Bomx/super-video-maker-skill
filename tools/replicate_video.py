#!/usr/bin/env python3
"""CLI wrapper around Replicate's bytedance/seedance-2.0 video model.

Always prints exactly one line to stdout starting with `RESULT: ` containing
JSON. Human logs go to stderr.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _find_repo_root(start: Path) -> Path:
    """Walk up from the skill dir to the project root (marked by .env or .git)."""
    for p in [start, *start.parents]:
        if (p / ".env").exists() or (p / ".git").exists():
            return p
    return start


SKILL_DIR = Path(__file__).resolve().parents[1]
# CWD wins if it has a .env (lets users invoke from any project), else walk up.
_CWD = Path.cwd().resolve()
REPO_ROOT = _CWD if (_CWD / ".env").exists() else _find_repo_root(SKILL_DIR)
DEFAULT_MODEL = "bytedance/seedance-2.0"
OUTPUT_DIR = REPO_ROOT / "output_videos"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def emit(payload: dict[str, Any]) -> None:
    print("RESULT: " + json.dumps(payload), flush=True)


def load_env() -> str:
    # Load .env from repo root first, then skill folder as fallback.
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        emit({"status": "failed", "error": "REPLICATE_API_TOKEN missing in .env", "model": DEFAULT_MODEL})
        sys.exit(2)
    return token


def resolve_reference(ref: str) -> Any:
    """Local paths are returned as open file handles; URLs pass through."""
    if ref.startswith(("http://", "https://")):
        return ref
    p = Path(ref).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"reference not found: {ref}")
    return open(p, "rb")


def cmd_generate(args: argparse.Namespace) -> None:
    load_env()
    import replicate  # imported after env is loaded

    inputs: dict[str, Any] = {
        "prompt": args.prompt,
        "aspect_ratio": args.aspect_ratio,
        "duration": args.duration,
        "resolution": args.resolution,
        "generate_audio": args.generate_audio,
        "reference_images": [resolve_reference(r) for r in (args.reference_image or [])],
        "reference_audios": [resolve_reference(r) for r in (args.reference_audio or [])],
        "reference_videos": [resolve_reference(r) for r in (args.reference_video or [])],
    }
    if args.seed is not None:
        inputs["seed"] = args.seed

    log(f"[replicate-video] running {args.model} duration={args.duration}s "
        f"resolution={args.resolution} ar={args.aspect_ratio} "
        f"refs(img/aud/vid)={len(inputs['reference_images'])}/"
        f"{len(inputs['reference_audios'])}/{len(inputs['reference_videos'])}")
    started = time.time()

    try:
        output = replicate.run(args.model, input=inputs)
    except Exception as exc:  # noqa: BLE001
        emit({"status": "failed", "error": str(exc), "model": args.model})
        sys.exit(1)

    # Replicate returns a FileOutput object (or list) for video models.
    file_obj = output[0] if isinstance(output, list) else output

    try:
        url = file_obj.url() if hasattr(file_obj, "url") else str(file_obj)
    except Exception:  # noqa: BLE001
        url = str(file_obj)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    local_path = OUTPUT_DIR / f"seedance_{int(time.time())}.mp4"
    try:
        if hasattr(file_obj, "read"):
            local_path.write_bytes(file_obj.read())
        else:
            import urllib.request
            urllib.request.urlretrieve(url, local_path)
    except Exception as exc:  # noqa: BLE001
        emit({
            "status": "succeeded_no_local",
            "error": f"download failed: {exc}",
            "output_url": url,
            "model": args.model,
        })
        sys.exit(0)

    elapsed = round(time.time() - started, 1)
    log(f"[replicate-video] done in {elapsed}s -> {local_path}")
    emit({
        "status": "succeeded",
        "output_url": url,
        "local_path": str(local_path.relative_to(REPO_ROOT)) if local_path.is_relative_to(REPO_ROOT) else str(local_path),
        "duration_s": args.duration,
        "resolution": args.resolution,
        "aspect_ratio": args.aspect_ratio,
        "model": args.model,
        "elapsed_s": elapsed,
    })


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="replicate_video.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="Generate a video clip with Seedance 2.0")
    g.add_argument("--prompt", required=True)
    g.add_argument("--aspect-ratio", default="16:9", choices=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"])
    g.add_argument("--duration", type=int, default=7, help="Clip length in seconds")
    g.add_argument("--resolution", default="1080p", choices=["480p", "720p", "1080p"])
    g.add_argument("--generate-audio", action="store_true")
    g.add_argument("--reference-image", action="append", help="Local path or URL. Repeat to add more.")
    g.add_argument("--reference-audio", action="append", help="Local path or URL. Repeat to add more.")
    g.add_argument("--reference-video", action="append", help="Local path or URL. Repeat to add more.")
    g.add_argument("--seed", type=int, default=None)
    g.add_argument("--model", default=DEFAULT_MODEL, help="Override model slug or pin a version (owner/name:hash).")
    g.set_defaults(func=cmd_generate)

    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

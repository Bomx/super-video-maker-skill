#!/usr/bin/env python3
"""CLI wrapper for fal.ai Seedance 2.0 video endpoints.

The project uses FALAI_API_KEY in .env. The fal SDK expects FAL_KEY, so this
tool maps FALAI_API_KEY -> FAL_KEY before calling fal_client.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

from dotenv import load_dotenv


DEFAULT_REFERENCE_MODEL = "bytedance/seedance-2.0/reference-to-video"
FAST_REFERENCE_MODEL = "bytedance/seedance-2.0/fast/reference-to-video"
TEXT_MODEL = "bytedance/seedance-2.0/text-to-video"
IMAGE_MODEL = "bytedance/seedance-2.0/image-to-video"


def _find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / ".env").exists() or (p / ".git").exists():
            return p
    return start


SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path.cwd().resolve() if (Path.cwd() / ".env").exists() else _find_repo_root(SKILL_DIR)
OUTPUT_DIR = REPO_ROOT / "output_videos"


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def emit(payload: dict[str, Any]) -> None:
    print("RESULT: " + json.dumps(payload), flush=True)


def load_env() -> None:
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(SKILL_DIR / ".env", override=False)
    fal_key = os.getenv("FAL_KEY") or os.getenv("FALAI_API_KEY")
    if not fal_key:
        emit(
            {
                "status": "failed",
                "error": "FALAI_API_KEY or FAL_KEY missing in .env",
                "provider": "fal.ai",
            }
        )
        sys.exit(2)
    os.environ["FAL_KEY"] = fal_key


def import_fal_client():
    try:
        import fal_client  # type: ignore
    except ImportError:
        emit(
            {
                "status": "failed",
                "error": "fal-client is not installed. Run: python3 -m pip install --user fal-client",
                "provider": "fal.ai",
            }
        )
        sys.exit(2)
    return fal_client


def error_detail(exc: Exception) -> dict[str, Any]:
    detail: dict[str, Any] = {"message": str(exc)}
    response = getattr(exc, "response", None)
    if response is not None:
        detail["status_code"] = getattr(response, "status_code", None)
        try:
            detail["response_text"] = response.text
        except Exception:  # noqa: BLE001
            pass
    return detail


def upload_if_local(fal_client, value: str, upload_repository: str) -> str:
    if value.startswith(("http://", "https://")):
        return value
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"reference file not found: {value}")
    log(f"[fal-seedance] upload {path.name} repository={upload_repository}")
    try:
        return fal_client.upload_file(path, repository=upload_repository)
    except Exception as exc:  # noqa: BLE001
        detail = error_detail(exc)
        response_text = str(detail.get("response_text") or "")
        if "Exhausted balance" in response_text:
            raise RuntimeError(
                "fal.ai rejected the upload because the account balance is exhausted. "
                "Top up at fal.ai/dashboard/billing, then retry. "
                f"Raw response: {response_text}"
            ) from exc
        raise RuntimeError(f"fal.ai upload failed: {json.dumps(detail)}") from exc


def choose_model(args: argparse.Namespace) -> str:
    if args.model:
        return args.model
    if args.mode == "text":
        return TEXT_MODEL
    if args.mode == "image":
        return IMAGE_MODEL
    if args.fast:
        return FAST_REFERENCE_MODEL
    return DEFAULT_REFERENCE_MODEL


def build_arguments(args: argparse.Namespace, fal_client) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "prompt": args.prompt,
        "resolution": args.resolution,
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "generate_audio": args.generate_audio,
    }
    if args.seed is not None:
        payload["seed"] = args.seed
    if args.end_user_id:
        payload["end_user_id"] = args.end_user_id

    image_urls = [
        upload_if_local(fal_client, p, args.upload_repository)
        for p in (args.reference_image or [])
    ]
    video_urls = [
        upload_if_local(fal_client, p, args.upload_repository)
        for p in (args.reference_video or [])
    ]
    audio_urls = [
        upload_if_local(fal_client, p, args.upload_repository)
        for p in (args.reference_audio or [])
    ]

    if args.mode == "image":
        if not image_urls:
            raise ValueError("--mode image requires --reference-image")
        payload["image_url"] = image_urls[0]
        if len(image_urls) > 1:
            payload["end_image_url"] = image_urls[1]
    elif args.mode == "reference":
        if image_urls:
            payload["image_urls"] = image_urls
        if video_urls:
            payload["video_urls"] = video_urls
        if audio_urls:
            payload["audio_urls"] = audio_urls
        if not image_urls and not video_urls and not audio_urls:
            raise ValueError("--mode reference requires at least one reference image/video/audio")
    elif image_urls or video_urls or audio_urls:
        raise ValueError("--mode text does not accept reference files; use --mode reference or --mode image")

    return payload


def extract_video_url(result: dict[str, Any]) -> str:
    video = result.get("video") or {}
    if isinstance(video, dict) and video.get("url"):
        return str(video["url"])
    if isinstance(result.get("videos"), list) and result["videos"]:
        first = result["videos"][0]
        if isinstance(first, dict) and first.get("url"):
            return str(first["url"])
    raise ValueError(f"Could not find video URL in fal result: {result}")


def cmd_generate(args: argparse.Namespace) -> None:
    load_env()
    fal_client = import_fal_client()
    model = choose_model(args)
    started = time.time()
    try:
        payload = build_arguments(args, fal_client)
        log(
            f"[fal-seedance] subscribe model={model} mode={args.mode} "
            f"duration={args.duration}s resolution={args.resolution} ar={args.aspect_ratio}"
        )
        result = fal_client.subscribe(
            model,
            arguments=payload,
            with_logs=True,
            client_timeout=args.client_timeout,
        )
        video_url = extract_video_url(result)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        local_path = OUTPUT_DIR / f"fal_seedance_{args.mode}_{int(time.time())}.mp4"
        urlretrieve(video_url, local_path)
        elapsed = round(time.time() - started, 1)
        emit(
            {
                "status": "succeeded",
                "provider": "fal.ai",
                "model": model,
                "mode": args.mode,
                "output_url": video_url,
                "local_path": str(local_path.relative_to(REPO_ROOT))
                if local_path.is_relative_to(REPO_ROOT)
                else str(local_path),
                "seed": result.get("seed"),
                "duration_s": args.duration,
                "resolution": args.resolution,
                "aspect_ratio": args.aspect_ratio,
                "generate_audio": args.generate_audio,
                "elapsed_s": elapsed,
            }
        )
    except Exception as exc:  # noqa: BLE001
        detail = error_detail(exc)
        response_text = str(detail.get("response_text") or "")
        if "Exhausted balance" in response_text:
            detail["action"] = "Top up the fal.ai account balance, then retry."
        emit(
            {
                "status": "failed",
                "provider": "fal.ai",
                "model": model,
                "error": detail["message"],
                "error_detail": detail,
            }
        )
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fal_seedance_video.py")
    sub = parser.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="Generate Seedance 2.0 video through fal.ai")
    gen.add_argument("--prompt", required=True)
    gen.add_argument(
        "--mode",
        default="reference",
        choices=["reference", "image", "text"],
        help="reference uses reference-to-video; image uses image-to-video; text uses text-to-video",
    )
    gen.add_argument("--fast", action="store_true", help="Use fast reference-to-video tier when mode=reference")
    gen.add_argument("--model", default="", help="Override fal model id")
    gen.add_argument("--reference-image", action="append", help="Local path or URL. Repeat to add up to 9 images.")
    gen.add_argument("--reference-video", action="append", help="Local path or URL. Repeat to add up to 3 videos.")
    gen.add_argument("--reference-audio", action="append", help="Local path or URL. Repeat to add up to 3 audio clips.")
    gen.add_argument(
        "--upload-repository",
        default=os.getenv("FAL_UPLOAD_REPOSITORY", "cdn"),
        choices=["cdn", "fal", "fal_v3"],
        help=(
            "Repository for local reference uploads. Defaults to cdn because "
            "fal_v3 requires the storage auth token endpoint and can fail with "
            "less actionable 403s when billing is locked."
        ),
    )
    gen.add_argument("--aspect-ratio", default="9:16", choices=["auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"])
    gen.add_argument("--duration", default="5", choices=["auto", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"])
    gen.add_argument("--resolution", default="720p", choices=["480p", "720p", "1080p"])
    gen.add_argument("--generate-audio", action=argparse.BooleanOptionalAction, default=False)
    gen.add_argument("--seed", type=int, default=None)
    gen.add_argument("--end-user-id", default="")
    gen.add_argument("--client-timeout", type=float, default=900.0)
    gen.set_defaults(func=cmd_generate)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

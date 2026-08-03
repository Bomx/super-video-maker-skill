#!/usr/bin/env python3
"""CLI wrapper for fal.ai Seedance video endpoints.

Defaults to Seedance 2.5. The project uses FALAI_API_KEY in .env. The fal SDK
expects FAL_KEY, so this tool maps FALAI_API_KEY -> FAL_KEY before calling
fal_client.

Version notes:
- 2.5 ships text-to-video, image-to-video and reference-to-video only. It has
  no fast/ or mini/ tier, so --fast and --mini pin that single call back to 2.0.
- 2.5 is an early-access model on fal and its terms require an end_user_id on
  every payload, so this tool always sends one (see resolve_end_user_id).
- Set SEEDANCE_VERSION=2.0 (or pass --seedance-version 2.0) to roll the whole
  skill back to the previous model without editing any recipe.
"""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import socket
import sys
import time
from pathlib import Path
from typing import Any
from urllib.request import urlretrieve

from dotenv import load_dotenv


DEFAULT_VERSION = "2.5"
DEFAULT_FALLBACK_VERSION = "2.0"
SUPPORTED_VERSIONS = ("2.5", "2.0")

# Only 2.0 publishes the cheaper distilled tiers.
TIERED_VERSIONS = ("2.0",)

MODE_ENDPOINTS = {
    "reference": "reference-to-video",
    "image": "image-to-video",
    "text": "text-to-video",
}

# Substrings that only ever appear in the canned example assets fal publishes in
# its endpoint schemas. Seeing one back means nothing was generated.
PLACEHOLDER_URL_MARKERS = (
    "falserverless/example_outputs",
    "storage.googleapis.com/falserverless/examples",
)


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


def load_dotenv_files() -> None:
    """Read the .env files only. Called before the parser is built so that
    SEEDANCE_VERSION and friends can be set in .env and still reach the
    argparse defaults, which are evaluated at parser-construction time."""
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(SKILL_DIR / ".env", override=False)


def load_env() -> None:
    load_dotenv_files()
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
    # Try the requested repository first, then fall back through the others.
    # fal's legacy "cdn"/"fal" storage endpoints have become unreliable
    # (DNS failures / HTTP 400 "Invalid storage type"); "fal_v3"
    # (v3.fal.media) is the current one. Auto-falling-back keeps the tool
    # working when the requested repository is down.
    order = [upload_repository] + [
        r for r in ("fal_v3", "cdn", "fal") if r != upload_repository
    ]
    last_detail: dict[str, Any] = {}
    for repo in order:
        log(f"[fal-seedance] upload {path.name} repository={repo}")
        try:
            return fal_client.upload_file(path, repository=repo)
        except Exception as exc:  # noqa: BLE001
            detail = error_detail(exc)
            last_detail = detail
            response_text = str(detail.get("response_text") or "")
            if "Exhausted balance" in response_text:
                # A billing block fails identically on every repository; stop now.
                raise RuntimeError(
                    "fal.ai rejected the upload because the account balance is exhausted. "
                    "Top up at fal.ai/dashboard/billing, then retry. "
                    f"Raw response: {response_text}"
                ) from exc
            log(
                f"[fal-seedance] upload via {repo} failed: "
                f"{detail.get('message')}; trying next repository"
            )
    raise RuntimeError(
        f"fal.ai upload failed for all repositories {order}: {json.dumps(last_detail)}"
    )


def resolve_end_user_id(explicit: str) -> str:
    """Seedance 2.5 is early-access and its terms require an end_user_id on every
    payload. An anonymous but stable identifier satisfies that, so fall back to
    one derived from the machine rather than sending nothing."""
    if explicit:
        return explicit
    from_env = os.getenv("FAL_END_USER_ID", "").strip()
    if from_env:
        return from_env
    try:
        fingerprint = f"{socket.gethostname()}:{getpass.getuser()}"
    except Exception:  # noqa: BLE001
        fingerprint = "super-video-maker"
    return "svm-" + hashlib.sha256(fingerprint.encode()).hexdigest()[:12]


def version_of(model: str) -> str:
    """Pull '2.5' out of 'bytedance/seedance-2.5/text-to-video'. Returns
    'custom' for a --model override that does not follow that shape."""
    for part in model.split("/"):
        if part.startswith("seedance-"):
            return part.removeprefix("seedance-")
    return "custom"


def choose_model(args: argparse.Namespace) -> str:
    if args.model:
        return args.model

    endpoint = MODE_ENDPOINTS[args.mode]
    version = args.seedance_version
    tier = "fast/" if args.fast else ("mini/" if args.mini else "")

    if tier and version not in TIERED_VERSIONS:
        # 2.5 has no distilled tiers. Honour the speed/cost request by pinning
        # this one call to 2.0 rather than silently billing the full model.
        tier_name = tier.rstrip("/")
        log(
            f"[fal-seedance] Seedance {version} has no {tier_name} tier; "
            f"pinning this call to 2.0 {tier_name}. "
            f"Drop --{tier_name} to stay on {version}."
        )
        version = "2.0"

    return f"bytedance/seedance-{version}/{tier}{endpoint}"


def build_arguments(args: argparse.Namespace, fal_client) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "prompt": args.prompt,
        "resolution": args.resolution,
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "generate_audio": args.generate_audio,
    }
    if args.bitrate_mode:
        payload["bitrate_mode"] = args.bitrate_mode
    if args.seed is not None:
        payload["seed"] = args.seed
    payload["end_user_id"] = resolve_end_user_id(args.end_user_id)

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


def is_placeholder_result(video_url: str) -> bool:
    """fal serves early-access models to unentitled accounts by handing back the
    canned example asset from the endpoint's own schema instead of generating
    anything. It returns HTTP 200 with a normal-looking body, so without this
    check every recipe would 'succeed' while quietly shipping stock footage."""
    return any(marker in video_url for marker in PLACEHOLDER_URL_MARKERS)


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

        if is_placeholder_result(video_url):
            requested = version_of(model)
            log(
                f"[fal-seedance] Seedance {requested} returned its canned example "
                f"clip instead of generating ({video_url}). This account is not "
                f"entitled to the {requested} early-access model."
            )
            if not args.fallback_version:
                emit(
                    {
                        "status": "failed",
                        "provider": "fal.ai",
                        "model": model,
                        "seedance_version": requested,
                        "error": (
                            f"Seedance {requested} is early-access and this fal account is "
                            "not entitled: fal returned the endpoint's example video instead "
                            "of generating. Request access on the model page at "
                            f"https://fal.ai/models/bytedance/seedance-{requested}/{MODE_ENDPOINTS[args.mode]} "
                            "(B2B-only terms, requires end_user_id), or rerun with "
                            "--seedance-version 2.0."
                        ),
                        "placeholder_url": video_url,
                    }
                )
                sys.exit(1)

            fallback_model = choose_model(
                argparse.Namespace(
                    **{
                        **vars(args),
                        "seedance_version": args.fallback_version,
                        "model": "",
                    }
                )
            )
            log(
                f"[fal-seedance] falling back to {fallback_model}. "
                "Pass --no-fallback to fail instead."
            )
            model = fallback_model
            result = fal_client.subscribe(
                model,
                arguments=payload,
                with_logs=True,
                client_timeout=args.client_timeout,
            )
            video_url = extract_video_url(result)
            if is_placeholder_result(video_url):
                raise RuntimeError(
                    f"Fallback model {model} also returned a placeholder clip: {video_url}"
                )
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        local_path = (
            OUTPUT_DIR
            / f"fal_seedance{version_of(model)}_{args.mode}_{int(time.time())}.mp4"
        )
        urlretrieve(video_url, local_path)
        elapsed = round(time.time() - started, 1)
        emit(
            {
                "status": "succeeded",
                "provider": "fal.ai",
                "model": model,
                "seedance_version": version_of(model),
                "requested_version": args.seedance_version,
                "fell_back": version_of(model) != args.seedance_version,
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

    gen = sub.add_parser("generate", help="Generate a Seedance video through fal.ai")
    gen.add_argument("--prompt", required=True)
    gen.add_argument(
        "--mode",
        default="reference",
        choices=["reference", "image", "text"],
        help="reference uses reference-to-video; image uses image-to-video; text uses text-to-video",
    )
    gen.add_argument(
        "--seedance-version",
        default=os.getenv("SEEDANCE_VERSION", DEFAULT_VERSION),
        choices=list(SUPPORTED_VERSIONS),
        help=(
            "Seedance model version. Defaults to 2.5 (override with the "
            "SEEDANCE_VERSION env var). Use 2.0 to roll back."
        ),
    )
    gen.add_argument(
        "--fast",
        action="store_true",
        help="Use the distilled fast tier. Only 2.0 has one, so this pins the call to 2.0.",
    )
    gen.add_argument(
        "--mini",
        action="store_true",
        help="Use the cheapest mini tier. Only 2.0 has one, so this pins the call to 2.0.",
    )
    gen.add_argument("--model", default="", help="Override fal model id")
    gen.add_argument(
        "--fallback-version",
        default=os.getenv("SEEDANCE_FALLBACK_VERSION", DEFAULT_FALLBACK_VERSION),
        choices=list(SUPPORTED_VERSIONS),
        help=(
            "Version to retry on when the requested one returns a placeholder "
            "clip because the account lacks early access. Default 2.0."
        ),
    )
    gen.add_argument(
        "--no-fallback",
        dest="fallback_version",
        action="store_const",
        const="",
        help="Fail loudly instead of retrying on the fallback version.",
    )
    gen.add_argument("--reference-image", action="append", help="Local path or URL. Repeat to add up to 9 images.")
    gen.add_argument("--reference-video", action="append", help="Local path or URL. Repeat to add up to 3 videos.")
    gen.add_argument("--reference-audio", action="append", help="Local path or URL. Repeat to add up to 3 audio clips.")
    gen.add_argument(
        "--upload-repository",
        default=os.getenv("FAL_UPLOAD_REPOSITORY", "fal_v3"),
        choices=["cdn", "fal", "fal_v3"],
        help=(
            "Repository for local reference uploads. Defaults to fal_v3 "
            "(v3.fal.media); the tool auto-falls back through the other "
            "repositories if the first upload fails. The legacy cdn/fal "
            "storage endpoints have become unreliable (DNS failures / "
            "'Invalid storage type')."
        ),
    )
    gen.add_argument("--aspect-ratio", default="9:16", choices=["auto", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"])
    gen.add_argument("--duration", default="5", choices=["auto", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"])
    gen.add_argument(
        "--resolution",
        default="720p",
        choices=["480p", "720p", "1080p", "4k"],
        help="4k is available on 2.5 and on the current 2.0 endpoints.",
    )
    gen.add_argument(
        "--bitrate-mode",
        default="",
        choices=["", "standard", "high"],
        help="Encoder bitrate. Leave unset to take the model default.",
    )
    gen.add_argument("--generate-audio", action=argparse.BooleanOptionalAction, default=False)
    gen.add_argument(
        "--seed",
        type=int,
        default=None,
        help=(
            "Passed through, but Seedance does not document a seed input and "
            "does not reject unknown fields. Drive character consistency with "
            "reference images, not with this flag."
        ),
    )
    gen.add_argument(
        "--end-user-id",
        default="",
        help=(
            "Required by Seedance 2.5's early-access terms. Defaults to "
            "FAL_END_USER_ID, then to a stable anonymous machine id."
        ),
    )
    gen.add_argument("--client-timeout", type=float, default=900.0)
    gen.set_defaults(func=cmd_generate)
    return parser


def main() -> None:
    load_dotenv_files()
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

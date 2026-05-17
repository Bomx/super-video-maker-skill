"""
HeyGen API Client — generates avatar videos for tutorial screencasts.

Uses the v2 API to create videos with the user's digital twin avatar,
green-screen background, and cloned voice. The green screen is later
removed via FFmpeg chroma key in tutorial_composer.py.

Endpoints used:
    GET  /v2/avatars              — list avatars (find digital twin)
    GET  /v2/voices               — list voices (find cloned voice)
    POST /v2/videos               — generate avatar video
    GET  /v2/videos/{video_id}    — poll generation status

Usage:
    from heygen_client import generate_avatar_video, poll_until_ready, download_video

    video_id = generate_avatar_video(script="Welcome to Distribb...")
    result = poll_until_ready(video_id)
    local_path = download_video(result["video_url"], "avatar_clip.mp4")
"""

import json
import logging
import os
import time
import argparse
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import requests
from dotenv import load_dotenv

def _find_project_root() -> Path:
    """Prefer the caller's project root, falling back to the skill folder."""
    cwd = Path.cwd().resolve()
    for path in [cwd, *cwd.parents]:
        if (path / ".env").exists() or (path / ".git").exists():
            return path
    tool_dir = Path(__file__).resolve().parent
    for path in [tool_dir, *tool_dir.parents]:
        if (path / ".env").exists() or (path / ".git").exists():
            return path
    return tool_dir


REPO_ROOT = _find_project_root()
load_dotenv(REPO_ROOT / ".env")
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)

logger = logging.getLogger("heygen_client")

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "")
HEYGEN_AVATAR_ID = os.getenv("HEYGEN_AVATAR_ID", "")
HEYGEN_VOICE_ID = os.getenv("HEYGEN_VOICE_ID", "")
HEYGEN_BASE_URL = "https://api.heygen.com"

GREEN_SCREEN_COLOR = "#00FF00"


def _headers():
    if not HEYGEN_API_KEY:
        raise ValueError("HEYGEN_API_KEY not set in .env")
    return {
        "x-api-key": HEYGEN_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# ═══════════════════════════════════════════════════════════
#  LIST AVATARS
# ═══════════════════════════════════════════════════════════

def list_avatars() -> List[Dict]:
    """Fetch all avatars from HeyGen (includes digital twins / instant avatars)."""
    logger.info("Fetching avatar list from HeyGen...")

    resp = requests.get(f"{HEYGEN_BASE_URL}/v2/avatars", headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json().get("data", {})

    avatars = data.get("avatars", [])
    talking_photos = data.get("talking_photos", [])

    logger.info(f"Found {len(avatars)} avatars + {len(talking_photos)} talking photos")
    return avatars + talking_photos


def find_avatar(avatar_id: str = "") -> Optional[Dict]:
    """Find a specific avatar by ID, or return the first instant/custom avatar."""
    target_id = avatar_id or HEYGEN_AVATAR_ID
    avatars = list_avatars()

    if target_id:
        for a in avatars:
            if a.get("avatar_id") == target_id:
                logger.info(f"Found avatar: {a.get('avatar_name', target_id)}")
                return a
        logger.warning(f"Avatar {target_id} not found in {len(avatars)} avatars")

    for a in avatars:
        if a.get("type") in ("instant", "custom", "digital_twin"):
            logger.info(f"Auto-selected avatar: {a.get('avatar_name')} (type={a.get('type')})")
            return a

    if avatars:
        logger.info(f"Falling back to first avatar: {avatars[0].get('avatar_name')}")
        return avatars[0]

    return None


# ═══════════════════════════════════════════════════════════
#  LIST VOICES
# ═══════════════════════════════════════════════════════════

def list_voices() -> List[Dict]:
    """Fetch all voices from HeyGen (includes cloned voices)."""
    logger.info("Fetching voice list from HeyGen...")

    resp = requests.get(f"{HEYGEN_BASE_URL}/v2/voices", headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json().get("data", {})

    voices = data.get("voices", [])
    logger.info(f"Found {len(voices)} voices")
    return voices


def find_voice(voice_id: str = "", preferred_name: str = "") -> Optional[Dict]:
    """Find a specific voice by ID, matching avatar name, or sensible fallback."""
    target_id = voice_id or HEYGEN_VOICE_ID
    voices = list_voices()

    if target_id:
        for v in voices:
            if v.get("voice_id") == target_id:
                logger.info(f"Found voice: {v.get('name', target_id)}")
                return v
        logger.warning(f"Voice {target_id} not found in {len(voices)} voices")

    if preferred_name:
        normalized = preferred_name.strip().lower()
        for v in voices:
            if (v.get("name") or "").strip().lower() == normalized:
                logger.info(f"Matched voice by avatar name: {v.get('name')} ({v.get('voice_id')})")
                return v

    for v in voices:
        if v.get("type") in ("cloned", "custom", "instant"):
            logger.info(f"Auto-selected cloned voice: {v.get('name')} (type={v.get('type')})")
            return v

    if voices:
        logger.info(f"Falling back to first voice: {voices[0].get('name')}")
        return voices[0]

    return None


# ═══════════════════════════════════════════════════════════
#  GENERATE AVATAR VIDEO
# ═══════════════════════════════════════════════════════════

def generate_avatar_video(
    script: str,
    avatar_id: str = "",
    voice_id: str = "",
    title: str = "Tutorial Avatar",
    resolution: str = "1080p",
    aspect_ratio: str = "16:9",
    background_color: str = GREEN_SCREEN_COLOR,
) -> str:
    """
    Create a HeyGen avatar video with green-screen background.

    Returns the video_id for polling.
    """
    aid = avatar_id or HEYGEN_AVATAR_ID
    vid = voice_id or HEYGEN_VOICE_ID
    avatar_name = ""

    if not aid:
        avatar = find_avatar()
        if not avatar:
            raise ValueError("No avatar available. Set HEYGEN_AVATAR_ID or create one at heygen.com")
        aid = avatar["avatar_id"]
        avatar_name = avatar.get("avatar_name", "")
    else:
        avatar = find_avatar(aid)
        avatar_name = avatar.get("avatar_name", "") if avatar else ""

    if not vid:
        voice = find_voice(preferred_name=avatar_name)
        if not voice:
            raise ValueError("No voice available. Set HEYGEN_VOICE_ID or create one at heygen.com")
        vid = voice["voice_id"]

    payload = {
        "avatar_id": aid,
        "voice_id": vid,
        "script": script,
        "title": title,
        "resolution": resolution,
        "aspect_ratio": aspect_ratio,
        "background": {
            "type": "color",
            "value": background_color,
        },
    }

    logger.info(f"Generating HeyGen avatar video...")
    logger.info(f"  Avatar ID: {aid}")
    logger.info(f"  Voice ID: {vid}")
    logger.info(f"  Script: {script[:80]}...")
    logger.info(f"  Resolution: {resolution}, Aspect: {aspect_ratio}")
    logger.info(f"  Background: {background_color} (green screen)")

    for attempt in range(3):
        try:
            resp = requests.post(
                f"{HEYGEN_BASE_URL}/v2/videos",
                headers=_headers(),
                json=payload,
                timeout=60,
            )
            resp.raise_for_status()
            result = resp.json().get("data", resp.json())
            video_id = result.get("video_id")

            if not video_id:
                raise ValueError(f"No video_id in response: {json.dumps(result)[:200]}")

            logger.info(f"Video generation started — video_id: {video_id}")
            return video_id

        except requests.HTTPError as e:
            logger.error(f"HeyGen API error (attempt {attempt+1}/3): {e.response.status_code} — {e.response.text[:300]}")
            if attempt < 2:
                time.sleep(5)
            else:
                raise
        except Exception as e:
            logger.error(f"HeyGen request failed (attempt {attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(5)
            else:
                raise


# ═══════════════════════════════════════════════════════════
#  POLL VIDEO STATUS
# ═══════════════════════════════════════════════════════════

def get_video_status(video_id: str) -> Dict:
    """Get current status of a HeyGen video generation job."""
    resp = requests.get(
        f"{HEYGEN_BASE_URL}/v2/videos/{video_id}",
        headers=_headers(),
        timeout=90,
    )
    resp.raise_for_status()
    return resp.json().get("data", resp.json())


def poll_until_ready(
    video_id: str,
    max_wait: int = 600,
    poll_interval: int = 10,
) -> Dict:
    """
    Poll HeyGen until the video is completed or failed.

    Returns the full status dict including video_url on success.
    Raises RuntimeError on failure or timeout.
    """
    logger.info(f"Polling video {video_id} (max {max_wait}s, every {poll_interval}s)...")
    start = time.time()

    while time.time() - start < max_wait:
        try:
            status = get_video_status(video_id)
        except requests.exceptions.RequestException as e:
            elapsed = int(time.time() - start)
            logger.warning(f"  [{elapsed}s] Status poll failed, retrying: {e}")
            time.sleep(poll_interval)
            continue

        state = status.get("status", "unknown")
        elapsed = int(time.time() - start)

        if state == "completed":
            video_url = status.get("video_url", "")
            duration = status.get("duration", 0)
            logger.info(f"Video ready after {elapsed}s — duration: {duration}s")
            logger.info(f"  URL: {video_url[:100]}...")
            return status

        if state == "failed":
            failure_code = status.get("failure_code", "UNKNOWN")
            failure_msg = status.get("failure_message", status.get("error", "No details"))
            raise RuntimeError(
                f"HeyGen video generation failed: [{failure_code}] {failure_msg}"
            )

        logger.info(f"  [{elapsed}s] Status: {state}...")
        time.sleep(poll_interval)

    raise RuntimeError(f"HeyGen video generation timed out after {max_wait}s (video_id={video_id})")


# ═══════════════════════════════════════════════════════════
#  DOWNLOAD VIDEO
# ═══════════════════════════════════════════════════════════

def download_video(video_url: str, local_path: str, timeout: int = 120) -> str:
    """Download a completed HeyGen video to a local file."""
    logger.info(f"Downloading HeyGen video to {local_path}...")

    os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)

    resp = requests.get(video_url, timeout=timeout, stream=True)
    resp.raise_for_status()

    with open(local_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    size_mb = os.path.getsize(local_path) / (1024 * 1024)
    logger.info(f"Downloaded: {local_path} ({size_mb:.1f} MB)")
    return local_path


# ═══════════════════════════════════════════════════════════
#  CONVENIENCE: FULL PIPELINE
# ═══════════════════════════════════════════════════════════

def create_avatar_clip(
    script: str,
    output_path: str,
    avatar_id: str = "",
    voice_id: str = "",
    max_wait: int = 600,
) -> Tuple[str, Dict]:
    """
    Full pipeline: generate avatar video, poll until ready, download.

    Returns (local_path, status_dict).
    """
    video_id = generate_avatar_video(
        script=script,
        avatar_id=avatar_id,
        voice_id=voice_id,
    )

    status = poll_until_ready(video_id, max_wait=max_wait)
    video_url = status.get("video_url", "")

    if not video_url:
        raise RuntimeError(f"No video_url in completed status: {json.dumps(status)[:200]}")

    download_video(video_url, output_path)

    return output_path, status


# ═══════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    parser = argparse.ArgumentParser(description="Generate a HeyGen avatar clip.")
    parser.add_argument(
        "--script",
        default=(
            "Welcome to this quick video tutorial. "
            "Let me show you the most important update in plain English."
        ),
    )
    parser.add_argument("--script-file")
    parser.add_argument("--output", default=str(REPO_ROOT / "demo_videos" / "heygen_avatar.mp4"))
    parser.add_argument("--avatar-id", default="")
    parser.add_argument("--voice-id", default="")
    parser.add_argument("--max-wait", type=int, default=600)
    args = parser.parse_args()

    script_text = args.script
    if args.script_file:
        script_text = Path(args.script_file).read_text(encoding="utf-8").strip()

    print("=" * 60)
    print("HeyGen Client")
    print(f"Project root: {REPO_ROOT}")
    print(f"Script chars: {len(script_text)}")
    print(f"Output: {args.output}")
    print("=" * 60)

    try:
        path, status = create_avatar_clip(
            script=script_text,
            output_path=args.output,
            avatar_id=args.avatar_id,
            voice_id=args.voice_id,
            max_wait=args.max_wait,
        )
        result = {
            "status": "succeeded",
            "local_path": path,
            "duration": status.get("duration"),
            "video_url": status.get("video_url"),
        }
        print(f"\nVideo saved: {path}")
        print("RESULT: " + json.dumps(result))
    except Exception as exc:
        print("RESULT: " + json.dumps({"status": "failed", "error": str(exc)}))
        raise

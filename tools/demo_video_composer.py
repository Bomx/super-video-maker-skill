"""
Demo Video Composer — Produces polished screen recording demos.

Takes a raw screen recording + events log and produces a final video with:
  1. Laptop mockup frame (MacBook-style bezel)
  2. Gradient background behind the laptop
  3. Zoom-in on click events with ripple effect
  4. Cursor highlight glow
  5. Smooth transitions between scenes
  6. ElevenLabs voiceover narration

Usage:
    from demo_video_composer import compose_demo_video

    result = compose_demo_video(
        raw_video_path="screen_recordings/recording_20260331.mp4",
        events_path="screen_recordings/recording_20260331_events.json",
        narration_script="Welcome to Distribb. Let me show you how easy it is...",
        output_path="demo_videos/final_demo.mp4",
    )

Dependencies: ffmpeg-python, Pillow, requests (for ElevenLabs)
"""

import base64
import json
import logging
import math
import os
import shutil
import subprocess
import tempfile
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import boto3
import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from dotenv import load_dotenv

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(REPO_ROOT, ".env"))

logger = logging.getLogger("demo_video_composer")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
DEFAULT_VOICE_ID = "hA4zGnmTwX2NQiTRMt7o"

DEMO_VIDEOS_DIR = os.path.join(REPO_ROOT, "demo_videos")

CANVAS_W = 2560
CANVAS_H = 1440

LAPTOP_SCREEN_W = 1920
LAPTOP_SCREEN_H = 1080

BEZEL_TOP = 40
BEZEL_SIDE = 18
BEZEL_BOTTOM = 18
BEZEL_CHIN = 28
BEZEL_RADIUS = 14
BEZEL_COLOR = (30, 30, 35, 255)
SCREEN_BORDER_COLOR = (10, 10, 12, 255)
CAMERA_DOT_COLOR = (50, 50, 55, 255)

GRADIENT_TOP = (15, 10, 40)
GRADIENT_BOTTOM = (5, 5, 20)
GRADIENT_ACCENT_1 = (255, 107, 0)
GRADIENT_ACCENT_2 = (180, 60, 220)

CLICK_RIPPLE_COLOR = (255, 107, 0)
CLICK_RIPPLE_MAX_RADIUS = 40
CLICK_RIPPLE_DURATION = 0.5

CURSOR_GLOW_COLOR = (255, 200, 100, 80)
CURSOR_GLOW_RADIUS = 20

ZOOM_FACTOR = 1.8
ZOOM_DURATION = 2.0
ZOOM_EASE_IN = 0.3
ZOOM_EASE_OUT = 0.3

FPS = 30


# ═══════════════════════════════════════════════════════════
#  ELEVENLABS TTS (reuses same pattern as typing_video_maker)
# ═══════════════════════════════════════════════════════════

def generate_narration(
    script: str,
    voice_id: str = DEFAULT_VOICE_ID,
    model_id: str = "eleven_v3",
    stability: float = 0.55,
    similarity_boost: float = 0.75,
    style: float = 0.35,
) -> Tuple[str, List[Dict]]:
    """
    Generate voiceover audio from script using ElevenLabs.
    Returns (audio_path, word_timestamps).
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not set in .env")

    logger.info(f"Generating narration | Voice: {voice_id} | {len(script)} chars / ~{len(script.split())} words")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    data = {
        "text": script,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
        },
    }

    for attempt in range(3):
        try:
            logger.info(f"ElevenLabs request attempt {attempt + 1}/3...")
            resp = requests.post(url, headers=headers, json=data, timeout=180)
            resp.raise_for_status()
            result = resp.json()
            logger.info("ElevenLabs response received")
            break
        except requests.HTTPError as e:
            logger.error(f"ElevenLabs HTTP error: {e.response.status_code} — {e.response.text[:200]}")
            if attempt < 2:
                time.sleep(5)
            else:
                raise
        except Exception as e:
            logger.error(f"ElevenLabs request failed: {e}")
            if attempt < 2:
                time.sleep(5)
            else:
                raise

    audio_bytes = base64.b64decode(result["audio_base64"])
    audio_path = os.path.join(tempfile.gettempdir(), f"narration_{uuid.uuid4().hex}.mp3")
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)
    logger.info(f"Narration audio saved: {audio_path} ({len(audio_bytes) / 1024:.1f} KB)")

    alignment = result.get("alignment", {})
    characters = alignment.get("characters", [])
    char_starts = alignment.get("character_start_times_seconds", [])
    char_ends = alignment.get("character_end_times_seconds", [])

    word_timestamps = _characters_to_words(characters, char_starts, char_ends)
    logger.info(f"Parsed {len(word_timestamps)} word timestamps, total duration: {word_timestamps[-1]['end']:.2f}s")

    return audio_path, word_timestamps


def _characters_to_words(characters, starts, ends):
    """Groups character-level alignment into word-level timestamps."""
    words = []
    current_word = ""
    word_start = None
    word_end = None

    for i, char in enumerate(characters):
        if char in (" ", "\n", "\t"):
            if current_word:
                words.append({"word": current_word, "start": word_start, "end": word_end})
                current_word = ""
                word_start = None
        else:
            if word_start is None:
                word_start = starts[i] if i < len(starts) else 0
            word_end = ends[i] if i < len(ends) else word_start
            current_word += char

    if current_word:
        words.append({"word": current_word, "start": word_start, "end": word_end})

    return words


# ═══════════════════════════════════════════════════════════
#  S3 UPLOAD (same pattern as typing_video_maker)
# ═══════════════════════════════════════════════════════════

def upload_to_s3(local_path: str, s3_key: str) -> Optional[str]:
    """Upload a file to S3 and return its public URL."""
    try:
        bucket = os.getenv("AWS_S3_BUCKET", "aiagentassets")
        region = os.getenv("AWS_REGION", "us-east-1")

        s3 = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )

        content_type = "video/mp4"
        if local_path.endswith(".ass"):
            content_type = "text/plain"
        elif local_path.endswith(".mp3"):
            content_type = "audio/mpeg"

        logger.info(f"Uploading to S3: s3://{bucket}/{s3_key}")
        s3.upload_file(
            local_path, bucket, s3_key,
            ExtraArgs={"ContentType": content_type, "ACL": "public-read"},
        )
        url = f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
        logger.info(f"S3 upload complete: {url}")
        return url
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════
#  ASS SUBTITLE GENERATION (synced to word timestamps)
# ═══════════════════════════════════════════════════════════

def _seconds_to_ass(ts: float) -> str:
    """Convert seconds to ASS timestamp format (H:MM:SS.CC)."""
    h, rem = divmod(ts, 3600)
    m, rem = divmod(rem, 60)
    s, cs = divmod(rem, 1)
    return f"{int(h):01d}:{int(m):02d}:{int(s):02d}.{int(cs * 100):02d}"


def create_subtitle_file(
    word_timestamps: List[Dict],
    width: int = CANVAS_W,
    height: int = CANVAS_H,
    position: str = "bottom",
) -> str:
    """
    Build an .ass subtitle file that highlights one word at a time.
    Words appear in white, the active word is highlighted in orange.
    Positioned at the bottom of the canvas (below the laptop mockup).
    """
    fd, path = tempfile.mkstemp(suffix=".ass")
    os.close(fd)

    position_styles = {
        "top": {"alignment": 8, "margin_v": 50},
        "middle": {"alignment": 5, "margin_v": 100},
        "bottom": {"alignment": 2, "margin_v": 40},
    }
    style_settings = position_styles.get(position.lower(), position_styles["bottom"])
    alignment = style_settings["alignment"]
    margin_v = style_settings["margin_v"]

    style_header = (
        "Format: Name, Fontname, Fontsize, PrimaryColour, "
        "SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
        "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, "
        "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
    )
    style_line = (
        f"Style: Default,Arial,48,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,"
        f"-1,0,0,0,100,100,0,0,1,3,2,{alignment},10,10,{margin_v},1"
    )

    highlight_color = "&H0000A5FF"  # Orange (BGR format for ASS)
    default_color = "&H00FFFFFF"

    dialogues = []
    num_words = len(word_timestamps)

    for i, word_info in enumerate(word_timestamps):
        start_val = max(0, word_info["start"])
        end_val = max(start_val + 0.1, word_info["end"])

        if end_val - start_val < 0.15:
            new_end = start_val + 0.15
            if i + 1 < num_words:
                next_start = word_timestamps[i + 1]["start"]
                if new_end > next_start:
                    new_end = next_start
            end_val = new_end

        start_time = _seconds_to_ass(start_val)
        end_time = _seconds_to_ass(end_val)

        current_styled = f"{{\\c{highlight_color}}}{word_info['word'].upper()}"

        text = current_styled
        if i + 1 < num_words:
            next_word = word_timestamps[i + 1]
            if next_word["start"] - end_val < 0.75:
                next_styled = f"{{\\c{default_color}}}{next_word['word'].upper()}"
                text = f"{current_styled} {next_styled}"

        dialogues.append(f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}")

    ass_contents = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}

[V4+ Styles]
{style_header}{style_line}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{chr(10).join(dialogues)}
"""
    with open(path, "w") as f:
        f.write(ass_contents.strip())

    logger.info(f"Subtitle file created: {path} ({len(dialogues)} dialogue lines)")
    return path


# ═══════════════════════════════════════════════════════════
#  BACKGROUND MUSIC DOWNLOAD
# ═══════════════════════════════════════════════════════════

SOUNDTRACKS_S3_BASE_URL = os.getenv("SOUNDTRACKS_S3_BASE_URL", "")
if not SOUNDTRACKS_S3_BASE_URL:
    try:
        _region = os.getenv("AWS_REGION", "us-east-1")
        _bucket = os.getenv("AWS_S3_BUCKET", "aiagentassets")
        if _bucket:
            SOUNDTRACKS_S3_BASE_URL = f"https://{_bucket}.s3.{_region}.amazonaws.com/soundtracks"
    except Exception:
        pass

DEFAULT_BGM_FILENAME = "phonk-tiktok-instagram-youtube-music-303287.mp3"


def download_bgm(filename: str = DEFAULT_BGM_FILENAME, timeout: int = 60) -> Optional[str]:
    """Download background music from S3 soundtracks bucket."""
    if not SOUNDTRACKS_S3_BASE_URL:
        logger.warning("SOUNDTRACKS_S3_BASE_URL not set — skipping BGM download")
        return None

    url = f"{SOUNDTRACKS_S3_BASE_URL.rstrip('/')}/{os.path.basename(filename)}"
    logger.info(f"Downloading BGM from S3: {url}")

    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=timeout, stream=True)
            resp.raise_for_status()

            local_path = os.path.join(tempfile.gettempdir(), f"bgm_{uuid.uuid4().hex}.mp3")
            with open(local_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            size_kb = os.path.getsize(local_path) / 1024
            logger.info(f"BGM downloaded: {local_path} ({size_kb:.0f} KB)")
            return local_path
        except Exception as e:
            logger.warning(f"BGM download attempt {attempt + 1}/3 failed: {e}")
            if attempt < 2:
                time.sleep(2)

    local_fallback = os.path.join(REPO_ROOT, "static", "audio", filename)
    if os.path.exists(local_fallback):
        logger.info(f"Using local BGM fallback: {local_fallback}")
        return local_fallback

    logger.warning("No BGM available — video will have narration only")
    return None


# ═══════════════════════════════════════════════════════════
#  GRADIENT BACKGROUND GENERATION
# ═══════════════════════════════════════════════════════════

def render_gradient_background(width=CANVAS_W, height=CANVAS_H):
    """Create a gradient background with accent glow orbs."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)

    for y in range(height):
        t = y / height
        r = int(GRADIENT_TOP[0] * (1 - t) + GRADIENT_BOTTOM[0] * t)
        g = int(GRADIENT_TOP[1] * (1 - t) + GRADIENT_BOTTOM[1] * t)
        b = int(GRADIENT_TOP[2] * (1 - t) + GRADIENT_BOTTOM[2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))

    glow1 = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow1_draw = ImageDraw.Draw(glow1)
    cx1, cy1 = int(width * 0.2), int(height * 0.3)
    for radius in range(400, 0, -2):
        alpha = int(20 * (radius / 400))
        glow1_draw.ellipse(
            [cx1 - radius, cy1 - radius, cx1 + radius, cy1 + radius],
            fill=(*GRADIENT_ACCENT_1, alpha),
        )
    img = Image.alpha_composite(img, glow1)

    glow2 = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow2_draw = ImageDraw.Draw(glow2)
    cx2, cy2 = int(width * 0.8), int(height * 0.7)
    for radius in range(350, 0, -2):
        alpha = int(15 * (radius / 350))
        glow2_draw.ellipse(
            [cx2 - radius, cy2 - radius, cx2 + radius, cy2 + radius],
            fill=(*GRADIENT_ACCENT_2, alpha),
        )
    img = Image.alpha_composite(img, glow2)

    return img


# ═══════════════════════════════════════════════════════════
#  LAPTOP MOCKUP FRAME
# ═══════════════════════════════════════════════════════════

def render_laptop_frame(screen_img):
    """
    Wraps a screenshot in a MacBook-style laptop bezel.
    Returns RGBA image of the laptop with screen content.
    """
    sw, sh = screen_img.size
    total_w = sw + BEZEL_SIDE * 2
    total_h = sh + BEZEL_TOP + BEZEL_BOTTOM + BEZEL_CHIN

    frame = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)

    draw.rounded_rectangle(
        [0, 0, total_w - 1, total_h - BEZEL_CHIN - 1],
        radius=BEZEL_RADIUS,
        fill=BEZEL_COLOR,
    )

    screen_x = BEZEL_SIDE
    screen_y = BEZEL_TOP
    draw.rectangle(
        [screen_x - 1, screen_y - 1, screen_x + sw, screen_y + sh],
        fill=SCREEN_BORDER_COLOR,
    )
    frame.paste(screen_img.convert("RGBA"), (screen_x, screen_y))

    cam_x = total_w // 2
    cam_y = BEZEL_TOP // 2
    cam_r = 4
    draw.ellipse(
        [cam_x - cam_r, cam_y - cam_r, cam_x + cam_r, cam_y + cam_r],
        fill=CAMERA_DOT_COLOR,
    )

    chin_y = total_h - BEZEL_CHIN
    draw.rounded_rectangle(
        [total_w // 2 - 60, chin_y, total_w // 2 + 60, total_h - 1],
        radius=4,
        fill=(40, 40, 45, 255),
    )

    shadow = Image.new("RGBA", (total_w + 60, total_h + 40), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        [30, 20, total_w + 30, total_h + 20],
        radius=BEZEL_RADIUS + 4,
        fill=(0, 0, 0, 100),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))

    result = Image.new("RGBA", (total_w + 60, total_h + 40), (0, 0, 0, 0))
    result = Image.alpha_composite(result, shadow)
    result.paste(frame, (30, 10), frame)

    return result


# ═══════════════════════════════════════════════════════════
#  CLICK RIPPLE EFFECT
# ═══════════════════════════════════════════════════════════

def render_click_ripple(width, height, x, y, progress):
    """
    Render a click ripple effect overlay.
    progress: 0.0 (start) to 1.0 (end).
    """
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    radius = int(CLICK_RIPPLE_MAX_RADIUS * progress)
    alpha = int(200 * (1 - progress))

    if alpha > 0 and radius > 0:
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            outline=(*CLICK_RIPPLE_COLOR, alpha),
            width=max(1, int(3 * (1 - progress))),
        )

        inner_r = max(1, radius // 3)
        inner_alpha = int(150 * (1 - progress))
        draw.ellipse(
            [x - inner_r, y - inner_r, x + inner_r, y + inner_r],
            fill=(*CLICK_RIPPLE_COLOR, inner_alpha),
        )

    return overlay


# ═══════════════════════════════════════════════════════════
#  CURSOR GLOW
# ═══════════════════════════════════════════════════════════

def render_cursor_glow(width, height, x, y):
    """Render a subtle glow around the cursor position."""
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for r in range(CURSOR_GLOW_RADIUS, 0, -1):
        alpha = int(CURSOR_GLOW_COLOR[3] * (r / CURSOR_GLOW_RADIUS))
        draw.ellipse(
            [x - r, y - r, x + r, y + r],
            fill=(CURSOR_GLOW_COLOR[0], CURSOR_GLOW_COLOR[1], CURSOR_GLOW_COLOR[2], alpha),
        )

    return overlay


# ═══════════════════════════════════════════════════════════
#  EASING FUNCTIONS
# ═══════════════════════════════════════════════════════════

def ease_in_out_cubic(t):
    """Smooth ease-in-out cubic curve."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2


def ease_out_cubic(t):
    return 1 - pow(1 - t, 3)


# ═══════════════════════════════════════════════════════════
#  ZOOM CROP
# ═══════════════════════════════════════════════════════════

def apply_zoom(frame_img, center_x, center_y, zoom_level, output_size):
    """
    Crop and scale a frame to simulate zoom-in.
    zoom_level: 1.0 = no zoom, 2.0 = 2x zoom.
    """
    fw, fh = frame_img.size
    ow, oh = output_size

    crop_w = int(fw / zoom_level)
    crop_h = int(fh / zoom_level)

    left = max(0, min(center_x - crop_w // 2, fw - crop_w))
    top = max(0, min(center_y - crop_h // 2, fh - crop_h))
    right = left + crop_w
    bottom = top + crop_h

    cropped = frame_img.crop((left, top, right, bottom))
    return cropped.resize((ow, oh), Image.LANCZOS)


# ═══════════════════════════════════════════════════════════
#  EXTRACT FRAMES FROM RAW VIDEO
# ═══════════════════════════════════════════════════════════

def extract_frames(video_path, output_dir, fps=FPS):
    """Extract frames from raw video using FFmpeg."""
    os.makedirs(output_dir, exist_ok=True)
    pattern = os.path.join(output_dir, "frame_%07d.png")

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"fps={fps}",
        "-q:v", "2",
        pattern,
    ]

    logger.info(f"Extracting frames at {fps}fps from {video_path}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        err_lines = [l for l in result.stderr.split("\n") if "Error" in l or "error" in l or "Invalid" in l]
        err_msg = "\n".join(err_lines) if err_lines else result.stderr[-500:]
        logger.error(f"Frame extraction failed: {err_msg}")
        raise RuntimeError(f"FFmpeg frame extraction failed: {err_msg}")

    frame_count = len([f for f in os.listdir(output_dir) if f.startswith("frame_")])
    logger.info(f"Extracted {frame_count} frames")
    return frame_count


# ═══════════════════════════════════════════════════════════
#  MAIN COMPOSER PIPELINE
# ═══════════════════════════════════════════════════════════

def compose_demo_video(
    raw_video_path: str,
    events_path: str,
    narration_script: str,
    output_path: Optional[str] = None,
    voice_id: str = DEFAULT_VOICE_ID,
    skip_narration: bool = False,
    add_subtitles: bool = True,
    subtitle_position: str = "bottom",
    add_bgm: bool = True,
    bgm_filename: str = DEFAULT_BGM_FILENAME,
    bgm_volume: float = 0.12,
    upload_s3: bool = True,
) -> Dict:
    """
    Compose a polished demo video from raw screen recording.

    Pipeline:
    1. Extract frames from raw recording
    2. Generate narration audio via ElevenLabs
    3. For each frame: gradient bg + laptop mockup + zoom/click effects
    4. Burn in word-synced subtitles
    5. Mix narration + background music
    6. Assemble frames + audio → final MP4
    7. Upload to S3

    Returns dict with: output_path, duration, s3_url, subtitle_path, etc.
    """
    import ffmpeg as ffmpeg_lib

    os.makedirs(DEMO_VIDEOS_DIR, exist_ok=True)

    ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not output_path:
        output_path = os.path.join(DEMO_VIDEOS_DIR, f"demo_{ts_str}.mp4")

    logger.info("=" * 60)
    logger.info("DEMO VIDEO COMPOSER (Enhanced)")
    logger.info(f"  Raw video: {raw_video_path}")
    logger.info(f"  Events: {events_path}")
    logger.info(f"  Subtitles: {add_subtitles} ({subtitle_position})")
    logger.info(f"  BGM: {add_bgm} (vol={bgm_volume})")
    logger.info(f"  S3 upload: {upload_s3}")
    logger.info(f"  Output: {output_path}")
    logger.info("=" * 60)

    with open(events_path, "r") as f:
        events_data = json.load(f)
    events = events_data.get("events", [])
    rec_width = events_data.get("width", 1920)
    rec_height = events_data.get("height", 1080)
    logger.info(f"Loaded {len(events)} events from recording")

    narration_audio = None
    word_timestamps = []
    if not skip_narration and narration_script:
        logger.info("Generating narration audio...")
        narration_audio, word_timestamps = generate_narration(narration_script, voice_id=voice_id)
        logger.info(f"Narration generated: {narration_audio}")

    bgm_path = None
    if add_bgm and narration_audio:
        logger.info("Downloading background music...")
        bgm_path = download_bgm(bgm_filename)

    work_dir = tempfile.mkdtemp(prefix="demo_composer_")
    raw_frames_dir = os.path.join(work_dir, "raw_frames")
    composed_frames_dir = os.path.join(work_dir, "composed_frames")
    os.makedirs(composed_frames_dir, exist_ok=True)

    temp_files = []
    result_data = {}

    try:
        frame_count = extract_frames(raw_video_path, raw_frames_dir, fps=FPS)
        total_duration = frame_count / FPS

        background = render_gradient_background(CANVAS_W, CANVAS_H)
        logger.info(f"Background gradient rendered: {CANVAS_W}x{CANVAS_H}")

        click_events = [e for e in events if e["type"] == "click"]
        zoom_windows = _build_zoom_windows(click_events, total_duration)
        logger.info(f"Built {len(zoom_windows)} zoom windows for click events")

        ripple_events = _build_ripple_events(click_events)
        logger.info(f"Built {len(ripple_events)} ripple effects")

        logger.info(f"Composing {frame_count} frames with effects...")
        for frame_idx in range(1, frame_count + 1):
            current_time = (frame_idx - 1) / FPS

            raw_frame_path = os.path.join(raw_frames_dir, f"frame_{frame_idx:07d}.png")
            if not os.path.exists(raw_frame_path):
                continue

            raw_frame = Image.open(raw_frame_path).convert("RGBA")

            if raw_frame.size != (rec_width, rec_height):
                raw_frame = raw_frame.resize((rec_width, rec_height), Image.LANCZOS)

            zoom_level, zoom_cx, zoom_cy = _get_zoom_at_time(current_time, zoom_windows)

            for ripple in ripple_events:
                rip_start = ripple["start"]
                rip_end = rip_start + CLICK_RIPPLE_DURATION
                if rip_start <= current_time <= rip_end:
                    progress = (current_time - rip_start) / CLICK_RIPPLE_DURATION
                    ripple_overlay = render_click_ripple(
                        rec_width, rec_height,
                        ripple["x"], ripple["y"],
                        progress,
                    )
                    raw_frame = Image.alpha_composite(raw_frame, ripple_overlay)

            active_click = _get_active_click(current_time, click_events)
            if active_click:
                glow = render_cursor_glow(
                    rec_width, rec_height,
                    active_click["x"], active_click["y"],
                )
                raw_frame = Image.alpha_composite(raw_frame, glow)

            if zoom_level > 1.01:
                raw_frame = apply_zoom(
                    raw_frame, zoom_cx, zoom_cy, zoom_level,
                    (rec_width, rec_height),
                )

            screen_for_laptop = raw_frame.resize(
                (LAPTOP_SCREEN_W, LAPTOP_SCREEN_H), Image.LANCZOS
            )
            laptop = render_laptop_frame(screen_for_laptop)

            canvas = background.copy()
            lw, lh = laptop.size
            lx = (CANVAS_W - lw) // 2
            ly = (CANVAS_H - lh) // 2
            canvas.paste(laptop, (lx, ly), laptop)

            composed_path = os.path.join(composed_frames_dir, f"frame_{frame_idx:07d}.png")
            canvas.convert("RGB").save(composed_path, optimize=False)

            if frame_idx % (FPS * 5) == 0:
                pct = frame_idx / frame_count * 100
                logger.info(f"  Composed frame {frame_idx}/{frame_count} ({pct:.0f}%) — {current_time:.1f}s")

        logger.info(f"All {frame_count} frames composed. Assembling final video...")

        # ── Step 1: Build video stream from composed frames ──
        frames_pattern = os.path.join(composed_frames_dir, "frame_%07d.png")
        video_stream = ffmpeg_lib.input(frames_pattern, framerate=FPS)

        # ── Step 2: Burn in subtitles if enabled ──
        subtitle_file = None
        if add_subtitles and word_timestamps:
            logger.info("Creating subtitle overlay...")
            subtitle_file = create_subtitle_file(
                word_timestamps,
                width=CANVAS_W,
                height=CANVAS_H,
                position=subtitle_position,
            )
            temp_files.append(subtitle_file)
            video_stream = ffmpeg_lib.filter(video_stream, "subtitles", subtitle_file)
            logger.info(f"Subtitles will be burned in from: {subtitle_file}")

        # ── Step 3: Build audio stream (narration + optional BGM) ──
        final_audio_stream = None
        if narration_audio and os.path.exists(narration_audio):
            narration_stream = ffmpeg_lib.input(narration_audio).audio

            if bgm_path and os.path.exists(bgm_path):
                logger.info(f"Mixing narration with BGM at {bgm_volume*100:.0f}% volume...")
                bgm_stream = (
                    ffmpeg_lib.input(bgm_path)
                    .audio
                    .filter("volume", bgm_volume)
                    .filter("apad")
                )
                final_audio_stream = ffmpeg_lib.filter(
                    [narration_stream, bgm_stream],
                    "amix",
                    inputs=2,
                    duration="first",
                )
                temp_files.append(bgm_path)
            else:
                final_audio_stream = narration_stream

        # ── Step 4: Encode final output ──
        if final_audio_stream is not None:
            (
                ffmpeg_lib
                .output(
                    video_stream,
                    final_audio_stream,
                    output_path,
                    vcodec="libx264",
                    pix_fmt="yuv420p",
                    preset="medium",
                    crf=18,
                    acodec="aac",
                    audio_bitrate="192k",
                    **{"shortest": None},
                )
                .overwrite_output()
                .run(quiet=True)
            )
        else:
            (
                ffmpeg_lib
                .output(
                    video_stream,
                    output_path,
                    vcodec="libx264",
                    pix_fmt="yuv420p",
                    preset="medium",
                    crf=18,
                )
                .overwrite_output()
                .run(quiet=True)
            )

        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Demo video assembled: {output_path} ({file_size_mb:.1f} MB)")

        # ── Step 5: Upload to S3 ──
        s3_url = None
        subtitle_s3_url = None
        if upload_s3:
            s3_key = f"public_videos/demo_{ts_str}.mp4"
            s3_url = upload_to_s3(output_path, s3_key)

            if subtitle_file and os.path.exists(subtitle_file):
                sub_s3_key = f"public_videos/demo_{ts_str}_subtitles.ass"
                subtitle_s3_url = upload_to_s3(subtitle_file, sub_s3_key)

        result_data = {
            "output_path": output_path,
            "duration_seconds": round(total_duration, 2),
            "frame_count": frame_count,
            "file_size_mb": round(file_size_mb, 2),
            "narration_audio_path": narration_audio,
            "events_count": len(events),
            "zoom_effects": len(zoom_windows),
            "s3_url": s3_url,
            "subtitle_file": subtitle_file,
            "subtitle_s3_url": subtitle_s3_url,
            "bgm_used": bgm_path is not None,
            "bgm_volume": bgm_volume if bgm_path else None,
        }

        logger.info(f"Result: {json.dumps({k: v for k, v in result_data.items() if v is not None}, indent=2)}")
        return result_data

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
        for tf in temp_files:
            try:
                if tf and os.path.exists(tf) and tf.startswith(tempfile.gettempdir()):
                    os.remove(tf)
            except Exception:
                pass
        logger.info("Cleaned up work directory and temp files")


# ═══════════════════════════════════════════════════════════
#  ZOOM WINDOW HELPERS
# ═══════════════════════════════════════════════════════════

def _build_zoom_windows(click_events, total_duration):
    """
    Build zoom windows from click events.
    Each click gets a zoom-in → hold → zoom-out window.
    """
    windows = []
    for evt in click_events:
        t = evt["timestamp"]
        ease_in_start = max(0, t - ZOOM_EASE_IN)
        hold_end = t + ZOOM_DURATION - ZOOM_EASE_IN - ZOOM_EASE_OUT
        ease_out_end = min(total_duration, hold_end + ZOOM_EASE_OUT)

        windows.append({
            "ease_in_start": ease_in_start,
            "hold_start": t,
            "hold_end": hold_end,
            "ease_out_end": ease_out_end,
            "center_x": evt["x"],
            "center_y": evt["y"],
            "zoom": ZOOM_FACTOR,
        })
    return windows


def _get_zoom_at_time(current_time, zoom_windows):
    """Get the zoom level and center point at a given time."""
    for w in zoom_windows:
        if w["ease_in_start"] <= current_time <= w["ease_out_end"]:
            if current_time < w["hold_start"]:
                t = (current_time - w["ease_in_start"]) / max(0.01, w["hold_start"] - w["ease_in_start"])
                factor = 1.0 + (w["zoom"] - 1.0) * ease_in_out_cubic(t)
            elif current_time <= w["hold_end"]:
                factor = w["zoom"]
            else:
                t = (current_time - w["hold_end"]) / max(0.01, w["ease_out_end"] - w["hold_end"])
                factor = w["zoom"] - (w["zoom"] - 1.0) * ease_in_out_cubic(t)
            return factor, w["center_x"], w["center_y"]
    return 1.0, 0, 0


def _build_ripple_events(click_events):
    """Build ripple effect data from click events."""
    return [
        {"start": evt["timestamp"], "x": evt["x"], "y": evt["y"]}
        for evt in click_events
    ]


def _get_active_click(current_time, click_events, window=1.5):
    """Find if there's a click event within `window` seconds of current time."""
    for evt in click_events:
        if abs(current_time - evt["timestamp"]) < window:
            return evt
    return None


# ═══════════════════════════════════════════════════════════
#  SCRIPT GENERATOR (uses Claude to write narration)
# ═══════════════════════════════════════════════════════════

def generate_narration_script(
    events_path: str,
    product_name: str = "Distribb",
    feature_description: str = "",
) -> str:
    """
    Use Claude to generate a narration script based on the recorded events.
    The script is designed for ElevenLabs TTS and timed to the recording.
    """
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package not installed")
        raise

    with open(events_path, "r") as f:
        events_data = json.load(f)

    events = events_data.get("events", [])
    duration = events_data.get("duration_seconds", 0)

    events_summary = []
    for evt in events:
        ts = evt.get("timestamp", 0)
        etype = evt.get("type", "")
        if etype == "click":
            events_summary.append(f"[{ts:.1f}s] Clicked on: {evt.get('element', 'element')}")
        elif etype == "navigate":
            events_summary.append(f"[{ts:.1f}s] Navigated to: {evt.get('url', '')}")
        elif etype == "type":
            events_summary.append(f"[{ts:.1f}s] Typed: {evt.get('text_preview', '')}")
        elif etype == "scroll":
            events_summary.append(f"[{ts:.1f}s] Scrolled {evt.get('direction', 'down')}")
        elif etype == "marker":
            events_summary.append(f"[{ts:.1f}s] Section: {evt.get('label', '')}")

    prompt = f"""Write a narration script for a {duration:.0f}-second product demo video of {product_name}.

The narration will be read by a professional voice (ElevenLabs TTS) and overlaid on the screen recording.

Feature being demonstrated: {feature_description or 'General product walkthrough'}

Here's what happens in the recording:
{chr(10).join(events_summary)}

Guidelines:
- Keep the tone conversational, confident, and professional
- Match the pacing to the recording duration (~{duration:.0f} seconds)
- Highlight key actions as they happen
- Start with a brief hook, walk through the demo, end with a call to action
- Do NOT include timestamps, stage directions, or formatting — just the spoken text
- Keep it concise: roughly {int(duration * 2.5)} words for natural pacing

Return ONLY the narration text, nothing else."""

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    script = response.content[0].text.strip()
    logger.info(f"Generated narration script: {len(script)} chars, ~{len(script.split())} words")
    return script


# ═══════════════════════════════════════════════════════════
#  CONVENIENCE: FULL PIPELINE
# ═══════════════════════════════════════════════════════════

def compose_from_recording(
    raw_video_path: str,
    events_path: str,
    narration_script: Optional[str] = None,
    auto_generate_script: bool = True,
    product_name: str = "Distribb",
    feature_description: str = "",
    voice_id: str = DEFAULT_VOICE_ID,
    output_path: Optional[str] = None,
    add_subtitles: bool = True,
    subtitle_position: str = "bottom",
    add_bgm: bool = True,
    bgm_filename: str = DEFAULT_BGM_FILENAME,
    bgm_volume: float = 0.12,
    upload_s3: bool = True,
) -> Dict:
    """
    Full pipeline: optionally auto-generate narration script, then compose
    with subtitles, background music, and S3 upload.
    """
    if not narration_script and auto_generate_script:
        logger.info("Auto-generating narration script from events...")
        narration_script = generate_narration_script(
            events_path,
            product_name=product_name,
            feature_description=feature_description,
        )
        logger.info(f"Script preview: {narration_script[:200]}...")

    return compose_demo_video(
        raw_video_path=raw_video_path,
        events_path=events_path,
        narration_script=narration_script or "",
        output_path=output_path,
        voice_id=voice_id,
        skip_narration=not narration_script,
        add_subtitles=add_subtitles,
        subtitle_position=subtitle_position,
        add_bgm=add_bgm,
        bgm_filename=bgm_filename,
        bgm_volume=bgm_volume,
        upload_s3=upload_s3,
    )


if __name__ == "__main__":
    import sys

    TEST_RAW_VIDEO = "screen_recordings/recording_test.mp4"
    TEST_EVENTS = "screen_recordings/recording_test_events.json"
    TEST_SCRIPT = (
        "Welcome to Distribb, the all-in-one SEO content engine. "
        "Watch how easy it is to create, optimize, and distribute content "
        "that actually ranks. Let me walk you through the dashboard."
    )

    raw_video = sys.argv[1] if len(sys.argv) > 1 else TEST_RAW_VIDEO
    events = sys.argv[2] if len(sys.argv) > 2 else TEST_EVENTS
    script = sys.argv[3] if len(sys.argv) > 3 else TEST_SCRIPT

    result = compose_demo_video(
        raw_video_path=raw_video,
        events_path=events,
        narration_script=script,
    )
    print(f"\nResult: {json.dumps(result, indent=2)}")

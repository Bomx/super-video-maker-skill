#!/usr/bin/env python3
"""
Build Remotion JSON props for CaptionedTalkingHead from Groq/Whisper words export.

Hardcode paths at the top, then run from repo root:
  python3 remotion-videos/build_caption_props.py

Outputs remotion-videos/public/render-props.json (gitignored pattern recommended).

Requires Python 3.9+.
"""
from __future__ import annotations

import json
import os

WORDS_JSON = os.getenv(
    "CAPTION_WORDS_JSON",
    "",
)

BROLL_JSON = os.getenv("CAPTION_BROLL_JSON", "").strip()

OUTPUT_JSON = os.path.join(os.path.dirname(__file__), "public", "render-props.json")

VIDEO_PUBLIC_RELATIVE = os.getenv(
    "CAPTION_MAIN_VIDEO_PUBLIC_PATH",
    "source/main.mp4",
)


def main() -> None:
    if not WORDS_JSON or not os.path.isfile(WORDS_JSON):
        raise SystemExit(
            "Set CAPTION_WORDS_JSON to your *_words.json (Groq verbose transcript)."
        )

    with open(WORDS_JSON, encoding="utf-8") as f:
        blob = json.load(f)

    words = blob.get("words") or []
    if not words:
        raise SystemExit("No words[] in JSON")

    word_tail = float(words[-1]["end"]) + 0.25
    probe = blob.get("duration_probe_sec")
    if probe is not None:
        duration_sec = float(probe)
    else:
        duration_sec = float(blob.get("duration_sec") or word_tail)
        duration_sec = max(duration_sec, word_tail)

    b_roll_clips: list = []
    if BROLL_JSON:
        if not os.path.isfile(BROLL_JSON):
            raise SystemExit(f"CAPTION_BROLL_JSON not found: {BROLL_JSON}")
        with open(BROLL_JSON, encoding="utf-8") as f:
            b_blob = json.load(f)
        if isinstance(b_blob, list):
            b_roll_clips = b_blob
        else:
            b_roll_clips = b_blob.get("bRollClips") or []

    props = {
        "durationInSeconds": duration_sec,
        "mainVideoSrc": VIDEO_PUBLIC_RELATIVE,
        "fps": 30,
        "width": 1920,
        "height": 1080,
        "accentHex": "#FF6B2C",
        "maxWordsPerLine": 8,
        "maxCharsPerLine": 46,
        "words": words,
        "bRollClips": b_roll_clips,
    }

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as out:
        json.dump(props, out, indent=2)

    print("Wrote", OUTPUT_JSON)
    print("Words:", len(words), "duration_sec:", round(duration_sec, 2))
    print("bRollClips:", len(b_roll_clips))


if __name__ == "__main__":
    main()

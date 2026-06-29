#!/usr/bin/env python3
"""
Generate the talking-head avatar clip for an avatar-insta-split reel via HeyGen,
then normalize to the project fps. Generic: avatar + voice come from CLI args or
the HEYGEN_AVATAR_ID / HEYGEN_VOICE_ID env vars (set them in your .env).

Usage:
    python3 gen_avatar.py --script-file script.txt --out avatar.mp4 \
        [--avatar-id ID] [--voice-id ID] [--aspect 9:16] [--fps 30]

Notes:
  * Tries the avatar's native background first; falls back to a flat light bg.
  * Saves the HeyGen video_id next to --out so a timed-out poll can be recovered
    instead of re-spending credits.
  * HeyGen meters API generation from a separate "API credit" pool (not the web
    studio plan). If you hit MOVIO_PAYMENT_INSUFFICIENT_CREDIT, top up API credits.
"""
import argparse, json, os, sys, subprocess, time

TOOLS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
sys.path.insert(0, TOOLS)
import heygen_client as hg  # noqa: E402
import requests  # noqa: E402

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script"); ap.add_argument("--script-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--avatar-id", default=os.getenv("HEYGEN_AVATAR_ID", ""))
    ap.add_argument("--voice-id", default=os.getenv("HEYGEN_VOICE_ID", ""))
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--resolution", default="1080p")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--max-wait", type=int, default=900)
    a = ap.parse_args()

    script = a.script
    if a.script_file:
        script = open(a.script_file, encoding="utf-8").read().strip()
    if not script:
        sys.exit("provide --script or --script-file")
    if not a.avatar_id:
        sys.exit("no avatar id: pass --avatar-id or set HEYGEN_AVATAR_ID in .env")

    base = {"avatar_id": a.avatar_id, "voice_id": a.voice_id, "script": script,
            "title": "avatar-insta-split", "resolution": a.resolution, "aspect_ratio": a.aspect}
    if not base["voice_id"]:
        base.pop("voice_id")  # let HeyGen match a default voice
    attempts = [dict(base), dict(base, background={"type": "color", "value": "#F2F2F2"})]

    video_id = None
    for i, payload in enumerate(attempts):
        r = requests.post(f"{hg.HEYGEN_BASE_URL}/v2/videos", headers=hg._headers(), json=payload, timeout=60)
        print(f"attempt {i+1}: HTTP {r.status_code} {r.text[:160]}")
        if r.status_code < 300:
            d = r.json().get("data", r.json()); video_id = d.get("video_id")
            if video_id:
                break
        time.sleep(2)
    if not video_id:
        sys.exit("RESULT: " + json.dumps({"status": "failed", "error": "no video_id (check avatar/voice id and API credits)"}))

    raw = a.out + ".raw.mp4"
    open(a.out + ".video_id.txt", "w").write(video_id)
    status = hg.poll_until_ready(video_id, max_wait=a.max_wait)
    hg.download_video(status.get("video_url"), raw)

    # normalize fps (HeyGen often renders 25fps); keep audio
    subprocess.run(["ffmpeg", "-y", "-i", raw, "-r", str(a.fps), "-c:v", "libx264",
                    "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", a.out], check=True)
    print("RESULT: " + json.dumps({"status": "succeeded", "video_id": video_id,
                                   "out": a.out, "raw": raw, "duration": status.get("duration")}))

if __name__ == "__main__":
    main()

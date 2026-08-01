#!/usr/bin/env python3
"""
Generate the talking-head avatar clip for an avatar-insta-split reel via HeyGen,
then normalize to the project fps.

Language handling (the De Vries / non-English fix):
  * --language English (default): UNCHANGED — HeyGen renders from the text script using
    HEYGEN_VOICE_ID (the existing path; English reels stay byte-identical).
  * --language <non-English>: the VO is generated with a DYNAMICALLY-PICKED ElevenLabs
    voice that matches the language (eleven_v3, via tools/elevenlabs_voice.py), uploaded
    to HeyGen, and the avatar is lip-synced to that audio via /v2/video/generate
    (voice type "audio"). Refuses to run without an explicit avatar id so a non-English
    project can never silently fall back to the English default voice.

Usage:
    python3 gen_avatar.py --script-file script.txt --out avatar.mp4 \
        [--avatar-id ID] [--voice-id ID] [--language Dutch] [--gender female] \
        [--el-voice-id ID] [--el-prefer NAME] [--aspect 9:16] [--fps 30]

Notes:
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
import elevenlabs_voice as el  # noqa: E402


def _normalize_fps(raw, out, fps):
    # HeyGen often renders 25fps; normalize, keep audio.
    subprocess.run(["ffmpeg", "-y", "-i", raw, "-r", str(fps), "-c:v", "libx264",
                    "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", out], check=True)


def gen_english(a, script):
    """Original path: HeyGen text-to-speech via the flat /v2/videos endpoint. Unchanged."""
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
    return video_id


def heygen_upload_audio(mp3_path):
    """Upload an mp3 to HeyGen; returns (asset_id, hosted_url). Verified contract 2026-06."""
    data = open(mp3_path, "rb").read()
    r = requests.post("https://upload.heygen.com/v1/asset", data=data,
                      headers={"x-api-key": hg.HEYGEN_API_KEY, "Content-Type": "audio/mpeg"}, timeout=120)
    r.raise_for_status()
    d = r.json().get("data", r.json())
    return d.get("id"), d.get("url")


def gen_nonenglish(a, script):
    """Non-English path: ElevenLabs VO (dynamic voice) -> HeyGen audio-driven avatar."""
    if not a.avatar_id:
        sys.exit("RESULT: " + json.dumps({"status": "failed", "error":
            "non-English VO needs an explicit avatar id (--avatar-id or HEYGEN_AVATAR_ID); "
            "refusing to fall back to the English default voice"}))
    # 1. pick a language-matched ElevenLabs voice (or honor an explicit override) + synthesize
    if a.el_voice_id:
        voice = {"voice_id": a.el_voice_id, "name": "(override)", "language": el.to_iso(a.language)}
    else:
        voice = el.pick_voice(a.language, gender=(a.gender or None), prefer=(a.el_prefer or None))
    print(f"ElevenLabs voice: {json.dumps(voice)}")
    mp3 = a.out + ".vo.mp3"
    res = el.tts(script, voice["voice_id"], mp3, model_id=a.el_model)
    print(f"ElevenLabs TTS: {json.dumps(res)}")
    # 2. upload the VO to HeyGen
    asset_id, asset_url = heygen_upload_audio(mp3)
    print(f"HeyGen audio asset: id={asset_id} url={asset_url}")
    # 3. audio-driven avatar render (the avatar lip-syncs the uploaded track)
    W, H = (1080, 1920) if a.aspect == "9:16" else (1920, 1080)
    payload = {
        "title": "avatar-insta-split (localized)",
        "dimension": {"width": W, "height": H},
        "video_inputs": [{
            "character": {"type": "avatar", "avatar_id": a.avatar_id, "avatar_style": "normal"},
            "voice": {"type": "audio", "audio_asset_id": asset_id},
        }],
    }
    r = requests.post(f"{hg.HEYGEN_BASE_URL}/v2/video/generate", headers=hg._headers(), json=payload, timeout=60)
    print(f"generate (audio_asset_id): HTTP {r.status_code} {r.text[:200]}")
    if r.status_code >= 300:  # fallback to the hosted audio_url
        payload["video_inputs"][0]["voice"] = {"type": "audio", "audio_url": asset_url}
        r = requests.post(f"{hg.HEYGEN_BASE_URL}/v2/video/generate", headers=hg._headers(), json=payload, timeout=60)
        print(f"generate (audio_url): HTTP {r.status_code} {r.text[:200]}")
        r.raise_for_status()
    d = r.json().get("data", r.json()); video_id = d.get("video_id")
    if not video_id:
        sys.exit("RESULT: " + json.dumps({"status": "failed", "error": f"no video_id: {r.text[:200]}"}))
    return video_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script"); ap.add_argument("--script-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--avatar-id", default=os.getenv("HEYGEN_AVATAR_ID", ""))
    ap.add_argument("--voice-id", default=os.getenv("HEYGEN_VOICE_ID", ""))
    ap.add_argument("--language", default=os.getenv("DFY_LANGUAGE", "English"),
                    help="Project language. English -> HeyGen text path (unchanged). Else ElevenLabs VO.")
    ap.add_argument("--gender", default="", help="bias the ElevenLabs voice pick (female|male)")
    ap.add_argument("--el-voice-id", default="", help="override the dynamic ElevenLabs voice pick")
    ap.add_argument("--el-prefer", default="", help="prefer an ElevenLabs voice whose name contains this")
    ap.add_argument("--el-model", default=el.PRIMARY_MODEL)
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
    if el.is_english(a.language) and not a.avatar_id:
        sys.exit("no avatar id: pass --avatar-id or set HEYGEN_AVATAR_ID in .env")

    if el.is_english(a.language):
        print("language=English -> HeyGen text voice (unchanged path)")
        video_id = gen_english(a, script)
    else:
        print(f"language={a.language} -> ElevenLabs VO + HeyGen audio-driven avatar")
        video_id = gen_nonenglish(a, script)

    raw = a.out + ".raw.mp4"
    open(a.out + ".video_id.txt", "w").write(video_id)
    status = hg.poll_until_ready(video_id, max_wait=a.max_wait)
    hg.download_video(status.get("video_url"), raw)
    _normalize_fps(raw, a.out, a.fps)
    print("RESULT: " + json.dumps({"status": "succeeded", "video_id": video_id,
                                   "out": a.out, "raw": raw, "duration": status.get("duration")}))


if __name__ == "__main__":
    main()

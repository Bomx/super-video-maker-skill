#!/usr/bin/env python3
"""ElevenLabs helper for NON-ENGLISH avatar VO.

When a project's language is not English, the avatar-insta-split pipeline can no longer
rely on the HeyGen text voice (which is the English default). This helper:
  1. picks a voice that matches the project language from ElevenLabs' shared voice library
     (dynamically — no hardcoded per-language voice id), and
  2. synthesizes the script with eleven_v3 (latest, 74 languages; falls back to
     eleven_multilingual_v2 if v3 is unavailable on the account).

English projects never call this — their path stays byte-identical (HeyGen TTS).

CLI:
    python3 elevenlabs_voice.py --language Dutch --gender female            # just pick a voice
    python3 elevenlabs_voice.py --language Dutch --text "Hallo" --out a.mp3 # pick + synthesize
"""
import argparse, json, os, urllib.request, urllib.error
from pathlib import Path

EL_BASE = "https://api.elevenlabs.io"
PRIMARY_MODEL = "eleven_v3"                 # latest, 74 langs (verified live 2026-06)
FALLBACK_MODEL = "eleven_multilingual_v2"   # 29 langs incl. nl/fr/de/es — wide account access

# free-text Projects.Language -> ISO 639-1. Unknown -> fail loud (never silently English).
LANG_MAP = {
    "english": "en", "dutch": "nl", "nederlands": "nl", "flemish": "nl", "vlaams": "nl",
    "french": "fr", "français": "fr", "francais": "fr", "spanish": "es", "español": "es",
    "espanol": "es", "german": "de", "deutsch": "de", "italian": "it", "italiano": "it",
    "portuguese": "pt", "português": "pt", "polish": "pl", "swedish": "sv", "danish": "da",
    "norwegian": "no", "finnish": "fi", "turkish": "tr", "czech": "cs", "greek": "el",
    "romanian": "ro", "hungarian": "hu", "russian": "ru", "ukrainian": "uk", "arabic": "ar",
    "hindi": "hi", "japanese": "ja", "korean": "ko", "chinese": "zh", "mandarin": "zh",
    "indonesian": "id", "vietnamese": "vi", "tagalog": "tl", "filipino": "tl",
}


def is_english(language: str) -> bool:
    """True for any English value/locale so it stays on the unchanged HeyGen text path:
    '', 'en', 'en-US'/'en_GB'/..., 'English', 'English (Australia)', etc."""
    s = (language or "").strip().lower()
    return s in ("", "en") or s.startswith("english") or s.startswith("en-") or s.startswith("en_")


def to_iso(language: str) -> str:
    s = (language or "").strip().lower()
    if not s:
        return "en"
    if len(s) == 2 and s.isalpha():
        return s
    if s not in LANG_MAP:
        raise SystemExit(f"unknown project language {language!r}; add it to LANG_MAP in elevenlabs_voice.py")
    return LANG_MAP[s]


def _key() -> str:
    k = os.getenv("ELEVENLABS_API_KEY")
    if k:
        return k
    for base in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parents[1]]:
        env = base / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.strip().startswith("ELEVENLABS_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("ELEVENLABS_API_KEY not set (env or .env)")


def _get(url: str):
    req = urllib.request.Request(url, headers={"xi-api-key": _key(), "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def pick_voice(language: str, gender: str = None, prefer: str = None) -> dict:
    """Pick a shared-library voice matching `language` (ISO or free-text).
    gender ('female'|'male') and prefer (substring of a voice name) bias the choice."""
    iso = to_iso(language)
    data = _get(f"{EL_BASE}/v1/shared-voices?language={iso}&page_size=40")
    voices = data.get("voices", data) if isinstance(data, dict) else data
    voices = [v for v in voices if v.get("language") == iso]
    if not voices:
        raise SystemExit(f"no ElevenLabs shared voices for language={iso}")

    def score(v):
        s = 0
        if prefer and prefer.lower() in (v.get("name") or "").lower():
            s += 100
        if gender and (v.get("gender") or "").lower() == gender.lower():
            s += 10
        if (v.get("accent") or "") == "standard":
            s += 2
        return s

    best = sorted(voices, key=score, reverse=True)[0]
    vid = best.get("voice_id")
    if not vid:
        raise SystemExit(f"ElevenLabs shared voice for {iso} ({best.get('name')!r}) has no voice_id")
    return {"voice_id": vid, "name": best.get("name"),
            "gender": best.get("gender"), "accent": best.get("accent"), "language": iso}


def tts(text: str, voice_id: str, out_path: str, model_id: str = PRIMARY_MODEL,
        stability: float = 0.4, similarity: float = 0.75) -> dict:
    """Synthesize `text` to mp3. Tries model_id, then FALLBACK_MODEL. Returns {out, model}."""
    models = [model_id] if model_id == FALLBACK_MODEL else [model_id, FALLBACK_MODEL]
    body_obj = {"text": text, "voice_settings": {"stability": stability, "similarity_boost": similarity}}
    last_err = None
    for m in models:
        body = json.dumps({**body_obj, "model_id": m}).encode()
        req = urllib.request.Request(
            f"{EL_BASE}/v1/text-to-speech/{voice_id}", data=body, method="POST",
            headers={"xi-api-key": _key(), "Content-Type": "application/json", "Accept": "audio/mpeg"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                audio = r.read()
            Path(out_path).parent.mkdir(parents=True, exist_ok=True)
            Path(out_path).write_bytes(audio)
            return {"out": out_path, "model": m, "bytes": len(audio)}
        except urllib.error.HTTPError as e:
            last_err = f"{e.code}: {e.read()[:300]!r}"
            continue
    raise SystemExit(f"ElevenLabs TTS failed for all models {models}: {last_err}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--language", required=True)
    ap.add_argument("--gender", default=None)
    ap.add_argument("--prefer", default=None)
    ap.add_argument("--text", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--model", default=PRIMARY_MODEL)
    a = ap.parse_args()
    if is_english(a.language):
        print(json.dumps({"english": True, "note": "English uses the HeyGen text path; ElevenLabs not used."}))
        raise SystemExit(0)
    v = pick_voice(a.language, a.gender, a.prefer)
    print("picked voice:", json.dumps(v))
    if a.text and a.out:
        res = tts(a.text, v["voice_id"], a.out, model_id=a.model)
        print("RESULT:", json.dumps({"status": "succeeded", "voice": v, **res}))

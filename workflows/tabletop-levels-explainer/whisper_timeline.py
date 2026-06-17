#!/usr/bin/env python3
"""Whisper each presenter clip (in chunks.json order) -> global word timing on the concatenated master.

Env: SVM_JOB. Reads chunks.json (for order) + assets/presenter/presenter_<id>.mp4.
Writes analysis/presenter_timing.json + analysis/presenter_words.txt.
"""
import json, os, subprocess, sys
from pathlib import Path
import whisper

JOB = Path(os.environ["SVM_JOB"])
PRES = JOB / "assets/presenter"
ORDER = [c["id"] for c in json.loads((JOB / "chunks.json").read_text())["chunks"]]

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=nw=1:nk=1", str(p)], capture_output=True, text=True).stdout.strip())

model = whisper.load_model("base.en")
offset, chunks, gw = 0.0, [], []
for ck in ORDER:
    clip = PRES / f"presenter_{ck}.mp4"
    if not clip.exists():
        print(f"MISSING {ck}", file=sys.stderr); continue
    wav = JOB / f"_p_{ck}.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(clip), "-vn", "-ac", "1", "-ar", "16000", str(wav)], check=True)
    d = dur(clip)
    r = model.transcribe(str(wav), language="en", word_timestamps=True, verbose=False)
    n = 0
    for s in r["segments"]:
        for w in s.get("words", []):
            gw.append({"w": w["word"].strip(), "start": round(w["start"] + offset, 3),
                       "end": round(w["end"] + offset, 3), "clip": ck}); n += 1
    chunks.append({"chunk": ck, "clip": str(clip), "offset": round(offset, 3), "dur": round(d, 3), "n_words": n})
    print(f"[whisper] {ck} off={offset:.2f} dur={d:.2f} words={n}", file=sys.stderr)
    offset += d

(JOB / "analysis").mkdir(exist_ok=True)
(JOB / "analysis/presenter_timing.json").write_text(json.dumps(
    {"order": ORDER, "total_dur": round(offset, 3), "chunks": chunks, "words": gw}, indent=2))
(JOB / "analysis/presenter_words.txt").write_text("\n".join(f"{w['start']:6.2f} {w['w']}" for w in gw))
print("RESULT: " + json.dumps({"status": "succeeded", "total_dur": round(offset, 2), "n_words": len(gw)}))

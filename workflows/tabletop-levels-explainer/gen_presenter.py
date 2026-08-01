#!/usr/bin/env python3
"""Generate one presenter chunk clip via Seedance reference-to-video with native audio.
Voice locked across chunks via --reference-audio (rules 44a/44b).

Env:
  SVM_JOB      job dir (contains chunks.json, assets/character/character_hero.png)
  SVM_ENV_DIR  dir containing the .env with FALAI_API_KEY (default: cwd)

chunks.json shape:
  {"character_preamble": "...She says: ", "style_suffix": " ...no captions...",
   "seed": 7777, "chunks": [{"id":"A","dur":10,"dialogue":"..."}, ...]}
"""
import argparse, json, os, subprocess, sys, shutil
from pathlib import Path

JOB = Path(os.environ["SVM_JOB"])
SKILL = Path(__file__).resolve().parents[2]
ENV_DIR = Path(os.environ.get("SVM_ENV_DIR", Path.cwd()))
FAL = str(SKILL / "tools/fal_seedance_video.py")
HERO = JOB / "assets/character/character_hero.png"

cfg = json.loads((JOB / "chunks.json").read_text())
by_id = {c["id"]: c for c in cfg["chunks"]}

ap = argparse.ArgumentParser()
ap.add_argument("--chunk", required=True)
ap.add_argument("--ref-audio", default="")
ap.add_argument("--resolution", default="720p")
a = ap.parse_args()

c = by_id[a.chunk]
prompt = cfg["character_preamble"] + '"' + c["dialogue"] + '"' + cfg["style_suffix"]
outdir = JOB / "assets/presenter"; outdir.mkdir(parents=True, exist_ok=True)

cmd = ["python3", FAL, "generate", "--mode", "reference",
       "--reference-image", str(HERO), "--prompt", prompt,
       "--duration", str(c["dur"]), "--resolution", a.resolution,
       "--aspect-ratio", "9:16", "--generate-audio", "--seed", str(cfg.get("seed", 7777))]
if a.ref_audio:
    cmd += ["--reference-audio", a.ref_audio]

print(f"[gen_presenter] chunk {a.chunk} dur={c['dur']} ref_audio={'yes' if a.ref_audio else 'no'}", file=sys.stderr)
proc = subprocess.run(cmd, cwd=str(ENV_DIR), capture_output=True, text=True)
sys.stderr.write(proc.stderr[-2000:])
line = [l for l in proc.stdout.splitlines() if l.startswith("RESULT:")]
if not line:
    print("RESULT: " + json.dumps({"status": "failed", "chunk": a.chunk, "stdout": proc.stdout[-500:]})); sys.exit(1)
res = json.loads(line[-1].split("RESULT: ", 1)[1])
if res.get("status") != "succeeded":
    print("RESULT: " + json.dumps({"status": "failed", "chunk": a.chunk, "fal": res})); sys.exit(1)
src = Path(res["local_path"])
if not src.is_absolute():
    src = ENV_DIR / src
dst = outdir / f"presenter_{a.chunk}.mp4"
shutil.copy(str(src), str(dst))
print("RESULT: " + json.dumps({"status": "succeeded", "chunk": a.chunk, "clip": str(dst), "seed": res.get("seed")}))

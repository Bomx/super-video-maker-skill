#!/usr/bin/env python3
"""Generate one craft b-roll clip via Seedance image-to-video (first-frame + last-frame steering). Silent.

Two --reference-image => image_url (first) + end_image_url (last); the motion prompt describes the action.

Env:
  SVM_JOB      job dir (output -> assets/broll/broll_<name>.mp4)
  SVM_ENV_DIR  dir containing the .env with FALAI_API_KEY (default: cwd)
"""
import argparse, json, os, subprocess, sys, shutil
from pathlib import Path

JOB = Path(os.environ["SVM_JOB"])
SKILL = Path(__file__).resolve().parents[2]
ENV_DIR = Path(os.environ.get("SVM_ENV_DIR", Path.cwd()))
FAL = str(SKILL / "tools/fal_seedance_video.py")

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--first", required=True)
ap.add_argument("--last", required=True)
ap.add_argument("--dur", default="4")
ap.add_argument("--prompt", required=True)
ap.add_argument("--resolution", default="720p")
ap.add_argument("--seed", default="4242")
a = ap.parse_args()

outdir = JOB / "assets/broll"; outdir.mkdir(parents=True, exist_ok=True)
cmd = ["python3", FAL, "generate", "--mode", "image",
       "--reference-image", a.first, "--reference-image", a.last,
       "--prompt", a.prompt, "--duration", str(a.dur),
       "--resolution", a.resolution, "--aspect-ratio", "9:16", "--no-generate-audio", "--seed", str(a.seed)]
print(f"[craft_clip] {a.name} dur={a.dur}", file=sys.stderr)
proc = subprocess.run(cmd, cwd=str(ENV_DIR), capture_output=True, text=True)
sys.stderr.write(proc.stderr[-1500:])
lines = [l for l in proc.stdout.splitlines() if l.startswith("RESULT:")]
if not lines:
    print("RESULT: " + json.dumps({"status": "failed", "name": a.name, "stdout": proc.stdout[-400:]})); sys.exit(1)
res = json.loads(lines[-1].split("RESULT: ", 1)[1])
if res.get("status") != "succeeded":
    print("RESULT: " + json.dumps({"status": "failed", "name": a.name, "fal": res})); sys.exit(1)
src = Path(res["local_path"])
if not src.is_absolute(): src = ENV_DIR / src
dst = outdir / f"broll_{a.name}.mp4"
shutil.copy(str(src), str(dst))
print("RESULT: " + json.dumps({"status": "succeeded", "name": a.name, "clip": str(dst)}))

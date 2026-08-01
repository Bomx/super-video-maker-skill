#!/usr/bin/env python3
"""Finalize: burn captions + mix ducked orchestral bed under the VO, loudness-normalize, export.

Env: SVM_JOB. Reads work/master_video.mp4, work/master_audio.m4a, assets/captions.ass,
assets/music/orchestral_bed.wav (optional). Writes exports/master.mp4.
"""
import json, os, subprocess, sys
from pathlib import Path

JOB = Path(os.environ["SVM_JOB"]); W = JOB / "work"
MVID = W / "master_video.mp4"; MAUD = W / "master_audio.m4a"
MUSIC = JOB / "assets/music/orchestral_bed.wav"; ASS = JOB / "assets/captions.ass"
OUT = JOB / "exports" / "master.mp4"; OUT.parent.mkdir(exist_ok=True)
ass_path = str(ASS).replace(":", "\\:")

if MUSIC.exists():
    filt = (f"[0:v]subtitles='{ass_path}'[vout];"
            f"[2:a]volume=0.22,afade=t=in:st=0:d=2[mus];"
            f"[mus][1:a]sidechaincompress=threshold=0.05:ratio=9:attack=5:release=350[mduck];"
            f"[1:a][mduck]amix=inputs=2:normalize=0:duration=first[mx];"
            f"[mx]loudnorm=I=-16:TP=-1.5:LRA=11[aout]")
    inputs = ["-i", str(MVID), "-i", str(MAUD), "-i", str(MUSIC)]
else:
    filt = f"[0:v]subtitles='{ass_path}'[vout];[1:a]loudnorm=I=-16:TP=-1.5:LRA=11[aout]"
    inputs = ["-i", str(MVID), "-i", str(MAUD)]

cmd = ["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", filt, "-map", "[vout]", "-map", "[aout]",
       "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "aac", "-b:a", "192k", "-shortest", str(OUT)]
p = subprocess.run(cmd, capture_output=True, text=True)
if p.returncode != 0:
    print(p.stderr[-2000:], file=sys.stderr); print("RESULT: " + json.dumps({"status": "failed"})); sys.exit(1)
dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(OUT)],
                     capture_output=True, text=True).stdout.strip()
print("RESULT: " + json.dumps({"status": "succeeded", "out": str(OUT), "dur": dur, "music": MUSIC.exists()}))

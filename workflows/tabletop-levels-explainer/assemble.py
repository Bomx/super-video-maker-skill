#!/usr/bin/env python3
"""Switch-assembly: continuous presenter audio + switched video (presenter <-> b-roll), beat-locked.

Env: SVM_JOB. Reads overlay_schedule.json + analysis/presenter_timing.json + assets/*.
Writes work/master_video.mp4, work/master_audio.m4a, exports/master_nocap.mp4.

overlay_schedule.json shape:
  {"master_dur": 89.8, "canvas": {"w":720,"h":1280,"fps":30},
   "presenter_concat": ["A","B",...],
   "broll": [{"asset":"broll_pyramid_draw","t0":3.5,"t1":5.9,"type":"clip"},
             {"asset":"agi_wiki","t0":42.3,"t1":44.6,"type":"still","dir":"receipts","kb":"in"}, ...]}
"""
import json, os, subprocess, sys
from pathlib import Path

JOB = Path(os.environ["SVM_JOB"])
A = JOB / "assets"; W = JOB / "work"; SEG = W / "segments"; SEG.mkdir(parents=True, exist_ok=True)
sched = json.loads((JOB / "overlay_schedule.json").read_text())
timing = json.loads((JOB / "analysis/presenter_timing.json").read_text())
CW, CH, FPS = sched["canvas"]["w"], sched["canvas"]["h"], sched["canvas"]["fps"]
DUR = timing["total_dur"]

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(" ".join(map(str, cmd)) + "\n" + p.stderr[-1500:] + "\n")
    return p.returncode == 0

concat_txt = W / "presenter_concat.txt"
concat_txt.write_text("".join(f"file '{A}/presenter/presenter_{ck}.mp4'\n" for ck in sched["presenter_concat"]))
PFULL = W / "presenter_full.mp4"
run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
     "-vf", f"scale={CW}:{CH}:force_original_aspect_ratio=increase,crop={CW}:{CH},fps={FPS}",
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "44100", str(PFULL)])
MAUD = W / "master_audio.m4a"
run(["ffmpeg", "-y", "-v", "error", "-i", str(PFULL), "-vn", "-c:a", "aac", "-b:a", "192k", str(MAUD)])

broll = sorted(sched["broll"], key=lambda b: b["t0"])
segs, cur = [], 0.0
for b in broll:
    if b["t0"] > cur + 0.04:
        segs.append({"kind": "presenter", "t0": cur, "t1": b["t0"]})
    segs.append({"kind": "broll", **b}); cur = max(cur, b["t1"])
if cur < DUR - 0.04:
    segs.append({"kind": "presenter", "t0": cur, "t1": DUR})

VF_FIT = f"scale={CW}:{CH}:force_original_aspect_ratio=increase,crop={CW}:{CH},fps={FPS},setpts=PTS-STARTPTS"

def find_asset(b):
    if b.get("type") == "still":
        return A / b.get("dir", "receipts") / f"{b['asset']}.png", "still"
    d = b.get("dir", "broll")
    clip = A / d / f"{b['asset']}.mp4"
    if clip.exists():
        return clip, "clip"
    name = b["asset"].replace("broll_", "")
    for cand in [A / "craft" / f"{name}_last.png", A / "craft" / "pyramid" / f"{name}.png"]:
        if cand.exists():
            return cand, "still"
    return clip, "missing"

manifest = []
for i, s in enumerate(segs):
    out = SEG / f"seg_{i:03d}.mp4"; dur = round(s["t1"] - s["t0"], 3)
    if dur <= 0.02:
        continue
    if s["kind"] == "presenter":
        run(["ffmpeg", "-y", "-v", "error", "-i", str(PFULL), "-ss", f"{s['t0']:.3f}", "-t", f"{dur:.3f}",
             "-an", "-vf", f"fps={FPS},scale={CW}:{CH},setpts=PTS-STARTPTS", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
        manifest.append((str(out), "presenter", dur)); continue
    path, kind = find_asset(s)
    if kind == "still":
        nf = max(1, int(round(dur * FPS)))
        z = "min(zoom+0.0010,1.14)" if s.get("kb") != "up" else "1.08"
        y = "ih/2-(ih/zoom/2)" if s.get("kb") != "up" else f"ih*0.12*(1-on/{nf})"
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-r", str(FPS), "-t", f"{dur:.3f}", "-i", str(path),
             "-vf", f"scale={CW*2}:-1,zoompan=z='{z}':d=1:x='iw/2-(iw/zoom/2)':y='{y}':s={CW}x{CH}:fps={FPS},setpts=PTS-STARTPTS",
             "-frames:v", str(nf), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
        manifest.append((str(out), f"still:{s['asset']}", dur))
    elif kind == "clip":
        run(["ffmpeg", "-y", "-v", "error", "-i", str(path),
             "-vf", f"{VF_FIT},tpad=stop_mode=clone:stop_duration=3", "-t", f"{dur:.3f}",
             "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)])
        manifest.append((str(out), f"clip:{s['asset']}", dur))
    else:
        sys.stderr.write(f"MISSING asset for {s['asset']}\n")

vlist = W / "video_concat.txt"; vlist.write_text("".join(f"file '{m[0]}'\n" for m in manifest))
MVID = W / "master_video.mp4"
run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(vlist),
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS), str(MVID)])
OUT = JOB / "exports" / "master_nocap.mp4"; OUT.parent.mkdir(exist_ok=True)
run(["ffmpeg", "-y", "-v", "error", "-i", str(MVID), "-i", str(MAUD), "-map", "0:v", "-map", "1:a",
     "-c:v", "copy", "-c:a", "aac", "-shortest", str(OUT)])
vd = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(OUT)],
                    capture_output=True, text=True).stdout.strip()
print("RESULT: " + json.dumps({"status": "succeeded", "out": str(OUT), "dur": vd, "segments": len(manifest),
                               "manifest": [(m[1], m[2]) for m in manifest]}))

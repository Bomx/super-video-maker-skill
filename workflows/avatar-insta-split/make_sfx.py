#!/usr/bin/env python3
"""Procedurally synthesize royalty-free SFX: keystroke, typing bed (2s), UI click.
All output 48kHz mono WAV. No external assets, no copyright."""
import subprocess, sys, os

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUT, exist_ok=True)
def run(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-1500:]); raise SystemExit(1)

KS = os.path.join(OUT, "keystroke.wav")
CLICK = os.path.join(OUT, "click.wav")
TYPING = os.path.join(OUT, "typing.wav")

# 1) single keystroke: short brown-noise burst, body+snap, fast decay (~45ms)
run(["ffmpeg","-y","-f","lavfi","-i","anoisesrc=d=0.05:c=brown:r=48000:a=0.9",
     "-af","highpass=f=350,lowpass=f=4000,afade=t=in:st=0:d=0.001,afade=t=out:st=0.006:d=0.042,volume=1.4",
     "-ac","1","-ar","48000", KS])

# 2) crisp UI click for scene cuts: high noise tick (~30ms) + tiny 2.2kHz ping
run(["ffmpeg","-y",
     "-f","lavfi","-i","anoisesrc=d=0.035:c=pink:r=48000:a=0.9",
     "-f","lavfi","-i","sine=frequency=2200:duration=0.02:sample_rate=48000",
     "-filter_complex",
     "[0:a]highpass=f=1900,lowpass=f=9000,afade=t=out:st=0.003:d=0.032,volume=1.6[n];"
     "[1:a]afade=t=out:st=0.002:d=0.018,volume=0.5[p];"
     "[n][p]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]",
     "-map","[a]","-ac","1","-ar","48000", CLICK])

# 3) typing bed: ~14 keystrokes at irregular intervals across 2.0s, varied volume
hits = [(30,0.7),(170,0.95),(300,0.6),(410,0.85),(560,1.0),(690,0.7),(830,0.9),
        (980,0.65),(1120,0.95),(1270,0.75),(1430,0.9),(1600,0.7),(1780,0.85),(1930,0.6)]
n = len(hits)
fc = f"[0:a]asplit={n}" + "".join(f"[s{i}]" for i in range(n)) + ";"
labels = []
for i,(ms,vol) in enumerate(hits):
    fc += f"[s{i}]adelay={ms}|{ms},volume={vol}[d{i}];"
    labels.append(f"[d{i}]")
fc += "".join(labels) + f"amix=inputs={n}:normalize=0,alimiter=limit=0.9,atrim=0:2.0,apad=whole_dur=2.0[a]"
run(["ffmpeg","-y","-i",KS,"-filter_complex",fc,"-map","[a]","-ac","1","-ar","48000", TYPING])

for f in (KS, CLICK, TYPING):
    d = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nokey=1:noprint_wrappers=1",f],capture_output=True,text=True).stdout.strip()
    print(f"{os.path.basename(f):14} dur={d}s")
print("SFX OK ->", OUT)

#!/usr/bin/env python3
"""
De-chop a talking-head clip: remove the dead-air pauses a TTS avatar inserts at
sentence breaks, keeping a short natural beat. Cuts VIDEO and AUDIO on the SAME
ranges so lip-sync is preserved (the hook just gets a natural jump-cut feel).

Use this on the avatar clip before build_vo_broll when the VO "goes silent" over
b-roll (the face isn't on screen to explain the pause).

Usage:
    python3 tighten_vo.py in.mp4 out.mp4 [keep_s=0.12] [thresh_db=-35] [min_gap=0.18]
"""
import sys, subprocess, re

def probe_dur(p):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nokey=1:noprint_wrappers=1",p], capture_output=True, text=True)
    return float(r.stdout.strip())

def main():
    src, out = sys.argv[1], sys.argv[2]
    KEEP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.12
    THR  = sys.argv[4] if len(sys.argv) > 4 else "-35"
    MIN  = sys.argv[5] if len(sys.argv) > 5 else "0.18"
    dur = probe_dur(src)

    # detect silence intervals
    r = subprocess.run(["ffmpeg","-i",src,"-af",f"silencedetect=n={THR}dB:d={MIN}","-f","null","-"],
                       capture_output=True, text=True)
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends   = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    gaps = list(zip(starts, ends))

    # remove the excess of each gap (keep KEEP seconds of it)
    removes = []
    for s, e in gaps:
        if e - s > KEEP:
            removes.append((s + KEEP, e))
    # keep-ranges = [0,dur] minus removes
    keeps = []; cur = 0.0
    for rs, re_ in removes:
        if rs > cur:
            keeps.append((cur, rs))
        cur = max(cur, re_)
    if cur < dur:
        keeps.append((cur, dur))
    # merge tiny adjacent
    keeps = [(round(a, 3), round(b, 3)) for a, b in keeps if b - a > 0.02]

    kept = sum(b - a for a, b in keeps)
    print(f"orig {dur:.2f}s -> kept {kept:.2f}s ({len(gaps)} gaps, removed {dur-kept:.2f}s of dead air)")

    sel = "+".join(f"between(t,{a},{b})" for a, b in keeps)
    vf = f"select='{sel}',setpts=N/FRAME_RATE/TB"
    af = f"aselect='{sel}',asetpts=N/SR/TB"
    subprocess.run(["ffmpeg","-y","-i",src,"-vf",vf,"-af",af,
                    "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p",
                    "-r","30","-c:a","aac","-ar","48000","-b:a","192k", out], check=True)
    print("RESULT:", out, "dur", round(probe_dur(out), 2))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
avatar-vo-broll — build a fullscreen "talking-head hook + voiceover-over-b-roll" reel
(Borja's most-successful IG format):

  hook  -> FULLSCREEN avatar talking head (letterboxed renders are blurred-filled)
  body  -> FULLSCREEN screen-capture b-roll clips, ONE per beat, while the avatar
           VOICEOVER keeps playing underneath
  close -> (optional) FULLSCREEN avatar again

Plus lower-third karaoke captions, a top badge that can swap (topic -> CTA), and the
typing bed + click-on-cut SFX. The avatar audio is one continuous track, so lip-sync
and VO stay aligned across the hard cuts.

Driven by a plan.json (see plan.example.json). Reuses the avatar-insta-split helpers
(caption builder, band detect, transcription) so the two recipes stay in sync.

Usage:
    python3 build_vo_broll.py plan.json [out.mp4]
"""
import json, os, sys, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SPLIT = os.path.normpath(os.path.join(HERE, "..", "avatar-insta-split"))
sys.path.insert(0, SPLIT)
import build_reel as br  # shared helpers: run, probe_float, rel, detect_band, build_chunks, render_pill, groq_transcribe

def main():
    plan_path = sys.argv[1]
    base = os.path.dirname(os.path.abspath(plan_path))
    plan = json.load(open(plan_path))
    out = sys.argv[2] if len(sys.argv) > 2 else br.rel(base, plan.get("output", "reel_final.mp4"))
    tmp = br.rel(base, plan.get("work_dir", "_work")); os.makedirs(tmp, exist_ok=True)

    cv = plan.get("canvas", {}); W = cv.get("w", 1080); H = cv.get("h", 1920); FPS = cv.get("fps", 30)
    avatar = br.rel(base, plan["avatar_clip"])
    cap = plan.get("caption", {}); CY = cap.get("cy", 1390)
    FONT = cap.get("font", "Arial-Bold"); PT = cap.get("pt", 56)
    captions_on = cap.get("enabled", True)

    # avatar content band (for the blurred-fill fullscreen hook/close)
    band = plan.get("avatar_content_band", "auto")
    by, bh = br.detect_band(avatar, W, H, tmp) if band == "auto" else (band["y"], band["h"])
    print(f"avatar content band: y={by} h={bh}")

    enc = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-an"]
    beats = plan["beats"]
    fb = [round(b["t0"] * FPS) for b in beats] + [round(beats[-1]["t1"] * FPS)]
    seg_dir = os.path.join(tmp, "seg"); os.makedirs(seg_dir, exist_ok=True)
    concat = os.path.join(tmp, "concat.txt"); cuts_ms = []

    # avatar fullscreen = blurred-filled content band (so a landscape/letterboxed render fills 9:16)
    av_fill = (f"[0:v]crop={W}:{bh}:0:{by},split[bnd1][bnd2];"
               f"[bnd1]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=26:2,eq=brightness=-0.05[bg];"
               f"[bnd2]setsar=1[fg];[bg][fg]overlay=0:{(H-bh)//2}[v]")

    with open(concat, "w") as cf:
        for i, b in enumerate(beats):
            n = fb[i + 1] - fb[i]
            if i > 0:
                cuts_ms.append(int(round(fb[i] / FPS * 1000)))
            outp = os.path.join(seg_dir, f"s{i:02d}.mp4")
            if b.get("type") == "broll":
                clip = br.rel(base, b["clip"])
                # cover-fill 9:16 (library clips are already 9:16 so this just upscales), loop to length
                subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-ss", str(b.get("clip_in", 0)), "-i", clip,
                                "-frames:v", str(n),
                                "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1",
                                *enc, outp], capture_output=True)
            else:  # avatar (hook / close)
                avss = f"{fb[i] / FPS:.4f}"
                subprocess.run(["ffmpeg", "-y", "-ss", avss, "-i", avatar, "-frames:v", str(n),
                                "-filter_complex", av_fill, "-map", "[v]", *enc, outp], capture_output=True)
            cf.write(f"file '{outp}'\n")
    body = os.path.join(tmp, "body.mp4")
    br.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", body])
    dur = br.probe_float(body, "format=duration")
    print(f"body: {int(dur*FPS)} frames, {len(beats)} beats, {len(cuts_ms)} cuts")

    # ── overlays: badges (sequence) + captions ──
    inputs = ["-i", body]; idx = 1; fc = []; prev = "0:v"
    for bd in plan.get("badges", []):
        png = br.rel(base, bd["png"])
        if not os.path.exists(png):
            continue
        inputs += ["-i", png]; bx, byp = bd.get("xy", [116, 150]); nxt = f"v{idx}"
        bw = bd.get("w")
        if bw:
            fc.append(f"[{idx}:v]scale={int(bw)}:-1,setsar=1[bd{idx}]")
            fc.append(f"[{prev}][bd{idx}]overlay={bx}:{byp}:enable='between(t,{bd['from']},{bd['to']})'[{nxt}]")
        else:
            fc.append(f"[{prev}][{idx}:v]overlay={bx}:{byp}:enable='between(t,{bd['from']},{bd['to']})'[{nxt}]")
        prev = nxt; idx += 1

    if captions_on:
        tr = br.rel(base, plan["transcript"]) if plan.get("transcript") else None
        if tr and os.path.exists(tr):
            words = json.load(open(tr))["words"]
        else:
            aud = os.path.join(tmp, "voice.mp3")
            br.run(["ffmpeg", "-y", "-i", avatar, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "96k", aud])
            words = br.groq_transcribe(aud, os.path.join(tmp, "transcript.json"))["words"]
        chunks = br.build_chunks(words, dur, cta_word=cap.get("cta_word", "comment"),
                                 cta_text=cap.get("cta_text", 'Comment "SKILL"'),
                                 fixups=cap.get("fixups", {}), cta_anchor=cap.get("cta_anchor"),
                                 cta_tail_s=cap.get("cta_tail_s", 2.5))
        capdir = os.path.join(tmp, "caps"); os.makedirs(capdir, exist_ok=True)
        pills = []
        for j, c in enumerate(chunks):
            if c["end"] - c["start"] < 0.08:
                continue
            png = os.path.join(capdir, f"c{j:03d}.png")
            pw, ph = br.render_pill(c["text"], png, FONT, PT, cap.get("padx", 34), cap.get("pady", 18), cap.get("radius", 30))
            pills.append({"png": png, "x": (W - pw) // 2, "y": CY - ph // 2, "start": c["start"], "end": c["end"]})
        for j in range(len(pills) - 1):
            pills[j]["end"] = min(pills[j]["end"], pills[j + 1]["start"])
        pills = [p for p in pills if p["end"] - p["start"] > 0.05]
        for p in pills:
            inputs += ["-i", p["png"]]; nxt = f"v{idx}"
            fc.append(f"[{prev}][{idx}:v]overlay={p['x']}:{p['y']}:enable='between(t,{round(p['start'],3)},{round(p['end'],3)})'[{nxt}]")
            prev = nxt; idx += 1

    # ── audio: continuous avatar VO + SFX ──
    sfx = plan.get("sfx", {})
    typing = br.rel(base, sfx.get("typing", os.path.join(SPLIT, "assets", "typing.wav")))
    click = br.rel(base, sfx.get("click", os.path.join(SPLIT, "assets", "click.wav")))
    if sfx.get("enabled", True) and (not os.path.exists(typing) or not os.path.exists(click)):
        mk = os.path.join(SPLIT, "make_sfx.py")
        if os.path.exists(mk):
            os.makedirs(os.path.dirname(typing) or ".", exist_ok=True)
            try: br.run(["python3", mk, os.path.dirname(typing) or "."])
            except SystemExit: pass
    use_sfx = sfx.get("enabled", True) and os.path.exists(typing)
    af = []
    ai = idx; inputs += ["-i", avatar]
    if use_sfx:
        inputs += ["-i", typing, "-i", click]
        af.append(f"[{ai}:a]volume=1.0[voice]")
        af.append(f"[{ai+1}:a]adelay=0|0,volume={sfx.get('typing_vol',0.13)}[typ]")
        labels = ["[voice]", "[typ]"]
        if cuts_ms and os.path.exists(click):
            af.append(f"[{ai+2}:a]asplit={len(cuts_ms)}" + "".join(f"[c{i}]" for i in range(len(cuts_ms))))
            for i, ms in enumerate(cuts_ms):
                af.append(f"[c{i}]adelay={ms}|{ms},volume={sfx.get('click_vol',0.38)}[k{i}]"); labels.append(f"[k{i}]")
        af.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]")
    else:
        af.append(f"[{ai}:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]")
    amap = "[a]"

    if not fc:
        fc = ["[0:v]copy[vout]"]; prev = "vout"
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(fc + af),
           "-map", f"[{prev}]", "-map", amap, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
           "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-ar", "48000", "-b:a", "192k",
           "-movflags", "+faststart", "-shortest", out]
    br.run(cmd)
    print("RESULT: " + json.dumps({"status": "succeeded", "out": out,
          "duration": round(br.probe_float(out, "format=duration"), 2), "beats": len(beats),
          "cuts": len(cuts_ms), "sfx": bool(use_sfx)}))

if __name__ == "__main__":
    main()

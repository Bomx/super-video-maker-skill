#!/usr/bin/env python3
"""
avatar-insta-split — build an Instagram-style split-screen reel:
  top ~53%  = screen-recording b-roll (cuts per beat)
  bottom ~47% = avatar / talking head (auto-cropped from its content band)
  + karaoke caption pills on the seam, optional hook badge,
  + typing SFX over the first ~2s (very low) and a click on every b-roll cut.

Everything is driven by a plan.json (see plan.example.json). Generic: the avatar
clip + b-roll + beat map are inputs, so it works for any creator/topic.

Usage:
    python3 build_reel.py plan.json [out.mp4]

Requires: ffmpeg/ffprobe, ImageMagick (`magick`), and GROQ_API_KEY in the env or
project .env (only when the plan has no "transcript" and captions are enabled).
"""
import json, os, sys, subprocess, re, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))

# ───────────────────────── helpers ─────────────────────────
def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        sys.stderr.write((r.stderr or "")[-2000:] + "\n")
        raise SystemExit(f"command failed: {' '.join(map(str, cmd))[:160]}")
    return r

def probe_float(path, entry):
    r = subprocess.run(["ffprobe","-v","error","-show_entries",entry,
        "-of","default=nokey=1:noprint_wrappers=1",path], capture_output=True, text=True)
    return float((r.stdout.strip().splitlines() or ["0"])[0])

def probe_dim(path, entry):
    """Probe a single video/image-stream dimension (entry='stream=width'|'stream=height')."""
    r = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries",entry,
        "-of","default=nokey=1:noprint_wrappers=1",path], capture_output=True, text=True)
    try:
        return float((r.stdout.strip().splitlines() or ["0"])[0])
    except ValueError:
        return 0.0

def rel(base_dir, p):
    if not p: return p
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(base_dir, p))

# ───────────────────────── groq transcription ─────────────────────────
def load_groq_key():
    if os.getenv("GROQ_API_KEY"): return os.getenv("GROQ_API_KEY")
    # walk up for a .env with GROQ_API_KEY
    d = os.getcwd()
    for path in [d, *[os.path.dirname(d)]] + [HERE, *_parents(HERE)]:
        env = os.path.join(path, ".env")
        if os.path.exists(env):
            for line in open(env):
                if line.strip().startswith("GROQ_API_KEY="):
                    return line.split("=",1)[1].strip().strip('"').strip("'")
    raise SystemExit("captions need GROQ_API_KEY (env or .env) or a precomputed plan['transcript']")

def _parents(p):
    out=[];
    while p and p != os.path.dirname(p): p=os.path.dirname(p); out.append(p)
    return out

def groq_transcribe(audio_path, out_json):
    key = load_groq_key()
    boundary = "----svmboundary7f3a2b"
    body = b""
    for k,v in {"model":"whisper-large-v3","response_format":"verbose_json","temperature":"0"}.items():
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for g in ("word","segment"):
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"timestamp_granularities[]\"\r\n\r\n{g}\r\n".encode()
    data = open(audio_path,"rb").read()
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"a.mp3\"\r\nContent-Type: audio/mpeg\r\n\r\n".encode()
    body += data + b"\r\n" + f"--{boundary}--\r\n".encode()
    req = urllib.request.Request("https://api.groq.com/openai/v1/audio/transcriptions", data=body,
        headers={"Authorization":f"Bearer {key}","Content-Type":f"multipart/form-data; boundary={boundary}",
                 "User-Agent":"Mozilla/5.0","Accept":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        result = json.loads(resp.read().decode())
    json.dump(result, open(out_json,"w"), indent=2)
    return result

# ───────────────────────── avatar content band ─────────────────────────
def detect_band(avatar, w, h, tmp):
    """Return (band_y, band_h): the non-letterbox content band of the avatar clip.
    Falls back to the full frame when no uniform bars are found."""
    frame = os.path.join(tmp, "_band_probe.png")
    run(["ffmpeg","-y","-ss","1.0","-i",avatar,"-frames:v","1",frame])
    # NB: no +repage (it resets the page offset); %Y prints a signed value.
    r = subprocess.run(["magick",frame,"-fuzz","6%","-trim","-format","%h|%Y","info:"],
                       capture_output=True, text=True)
    try:
        bh_s, by_s = r.stdout.strip().split("|"); bh, by = int(bh_s), int(by_s)
        if bh < h*0.15 or bh > h*0.99:   # implausible trim (likely no bars) -> full frame
            return 0, h
        return by, bh
    except Exception:
        return 0, h

# ───────────────────────── caption pills ─────────────────────────
def build_chunks(words, end, cta_word="comment", cta_text='Comment "SEO"',
                 fixups=None, cta_anchor=None, cta_tail_s=2.5):
    fixups = fixups or {}
    clean = lambda x: x.strip()
    chunks, cur, cstart = [], [], None
    for wd in words:
        tok = clean(wd["word"])
        if not tok: continue
        if cstart is None: cstart = wd["start"]
        cur.append(tok); cend = wd["end"]
        if (cend-cstart) >= 0.55 or len(cur) >= 3 or re.search(r"[.,!?]$", tok):
            chunks.append({"text":" ".join(cur),"start":cstart,"end":cend}); cur,cstart=[],None
    if cur: chunks.append({"text":" ".join(cur),"start":cstart,"end":words[-1]["end"]})
    for i in range(1,len(chunks)):
        if chunks[i]["start"] < chunks[i-1]["end"]: chunks[i]["start"]=chunks[i-1]["end"]
    for i in range(len(chunks)-1): chunks[i]["end"]=chunks[i+1]["start"]
    for c in chunks:
        if c["end"]<=c["start"]: c["end"]=c["start"]+0.25
    for i in range(len(chunks)-1): chunks[i]["end"]=min(chunks[i]["end"], chunks[i+1]["start"])
    # text fixups (e.g., Whisper mis-hears) on the rendered caption text
    for c in chunks:
        for a,b in fixups.items(): c["text"]=re.sub(a,b,c["text"])
    # held CTA pill. Two modes:
    #  - word anchor (default, English): find the chunk starting with cta_word and hold it.
    #  - tail anchor (language/platform-agnostic): hold cta_text over the final cta_tail_s
    #    seconds regardless of wording — for non-English VO and YouTube brand callouts where
    #    there is no English "comment" trigger word to match.
    if cta_text and cta_anchor == "tail":
        if not chunks:
            return [{"text": cta_text, "start": max(end - cta_tail_s, 0.0), "end": end}]
        cs = max(end - cta_tail_s, chunks[0]["start"])
        kept = [c for c in chunks if c["start"] < cs]
        if not kept:  # VO shorter than the tail window -> keep body, convert only the last chunk
            kept = chunks[:-1]; cs = chunks[-1]["start"]
        for c in kept:
            if c["end"] > cs: c["end"] = cs
        chunks = kept + [{"text":cta_text,"start":cs,"end":end}]
    elif cta_word:
        idx = next((i for i,c in enumerate(chunks) if c["text"].lower().startswith(cta_word)), None)
        if idx is not None:
            w0 = next((w for w in words if clean(w["word"]).lower().startswith(cta_word)), None)
            cs = w0["start"] if w0 else chunks[idx]["start"]
            if idx>0: chunks[idx-1]["end"]=min(chunks[idx-1]["end"], cs)
            chunks = chunks[:idx]+[{"text":cta_text,"start":cs,"end":end}]
    return chunks

def render_pill(text, path, font, pt, padx, pady, radius):
    info = run(["magick","-background","none","-fill","black","-font",font,"-pointsize",str(pt),
        f"label:{text}","-format","%w %h","info:"]).stdout.split()
    tw,th = int(info[0]), int(info[1]); pw,ph = tw+2*padx, th+2*pady; r=min(radius, ph//2)
    run(["magick","-size",f"{pw}x{ph}","xc:none","-fill","#ffffffF2",
        "-draw",f"roundrectangle 0,0 {pw-1},{ph-1} {r},{r}","-font",font,"-pointsize",str(pt),
        "-fill","#0a0a0a","-gravity","center","-annotate","+0+0",text,path])
    return pw, ph

# ───────────────────────── main ─────────────────────────
def main():
    plan_path = sys.argv[1]
    base = os.path.dirname(os.path.abspath(plan_path))
    plan = json.load(open(plan_path))
    out = sys.argv[2] if len(sys.argv)>2 else rel(base, plan.get("output","reel_final.mp4"))
    tmp = rel(base, plan.get("work_dir","_work")); os.makedirs(tmp, exist_ok=True)

    cv = plan.get("canvas",{}); W=cv.get("w",1080); H=cv.get("h",1920); FPS=cv.get("fps",30)
    sp = plan.get("split",{}); TOP_H=sp.get("broll_top_h",1024); BOT_H=sp.get("avatar_bottom_h",H-TOP_H)
    avatar = rel(base, plan["avatar_clip"]); broll = rel(base, plan["broll_source"])
    cap = plan.get("caption",{}); SEAM_CY=cap.get("seam_cy",TOP_H-18)
    FONT=cap.get("font","Arial-Bold"); PT=cap.get("pt",56)
    captions_on = cap.get("enabled", True)

    # avatar content band
    band = sp.get("avatar_content_band","auto")
    if band == "auto":
        by, bh = detect_band(avatar, W, H, tmp)
    else:
        by, bh = band["y"], band["h"]
    print(f"avatar content band: y={by} h={bh}")
    BOT = (f"crop={W}:{bh}:0:{by},scale={W}:{BOT_H}:force_original_aspect_ratio=increase,"
           f"crop={W}:{BOT_H},setsar=1")

    # ── segments (frame-aligned) ──
    beats = plan["beats"]
    fbounds = [round(b["t0"]*FPS) for b in beats] + [round(beats[-1]["t1"]*FPS)]
    seg_dir = os.path.join(tmp,"seg"); os.makedirs(seg_dir, exist_ok=True)
    concat = os.path.join(tmp,"concat.txt"); cuts_ms=[]
    enc = ["-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-r",str(FPS),"-an"]
    # The b-roll is either a screen RECORDING (video) or a tall article SCREENSHOT (image).
    # For an image we drive a controllable, frame-timed vertical SCROLL: per-beat
    # `scroll_from`/`scroll_to` are pixel offsets in the article once scaled to the canvas
    # width W, so the article moves at an explicit, tunable speed (and a beat with
    # scroll_from=0 frames the headline). When a beat has no scroll_* fields the legacy
    # static `crop` path is used, now aspect-preserving so the article can't be squashed.
    broll_is_img = os.path.splitext(broll)[1].lower() in (".png",".jpg",".jpeg",".webp",".bmp")
    bw_src = probe_dim(broll, "stream=width") or 1.0
    bh_src = probe_dim(broll, "stream=height") or 1.0
    Hs = int(round(bh_src * W / bw_src))                    # article height once scaled to width W
    can_scroll = Hs > TOP_H                                 # too-short article can't be panned
    SCROLL_MAX = max(Hs - TOP_H - 2, 0)                     # -2px safety vs ffmpeg even-rounding
    def _sclamp(v): return max(0.0, min(float(v), SCROLL_MAX))
    print(f"broll: {'image' if broll_is_img else 'video'} {int(bw_src)}x{int(bh_src)} -> scaled H={Hs}, "
          f"scroll {'range 0..%d' % SCROLL_MAX if can_scroll else 'DISABLED (article <= region; cover-static)'}")
    with open(concat,"w") as cf:
        for i,b in enumerate(beats):
            f0,f1 = fbounds[i], fbounds[i+1]; n=f1-f0; D=max(n/FPS, 1e-3)
            if i>0: cuts_ms.append(int(round(f0/FPS*1000)))
            avss=f"{f0/FPS:.4f}"; outp=os.path.join(seg_dir,f"s{i:02d}.mp4")
            in_av = ["-ss",avss,"-i",avatar]
            if broll_is_img:
                in_br = ["-loop","1","-framerate",str(FPS),"-t",f"{D:.4f}","-i",broll]
            else:
                in_br = ["-ss",str(b.get("broll_in",0)),"-i",broll]
            scroll_beat = "scroll_from" in b and "scroll_to" in b
            if scroll_beat and can_scroll:
                y0=_sclamp(b["scroll_from"]); y1=_sclamp(b["scroll_to"])
                top=(f"[1:v]scale={W}:-2,setsar=1,"
                     f"crop={W}:{TOP_H}:0:{y0:.2f}+({y1:.2f}-{y0:.2f})*t/{D:.4f}[top]")
            elif scroll_beat:
                # article too short to scroll: cover the region (aspect-preserved), no pan
                top=(f"[1:v]scale={W}:{TOP_H}:force_original_aspect_ratio=increase,"
                     f"crop={W}:{TOP_H},setsar=1[top]")
            else:
                crop=b["crop"]
                top=(f"[1:v]crop={crop},scale={W}:{TOP_H}:force_original_aspect_ratio=increase,"
                     f"crop={W}:{TOP_H},setsar=1[top]")
            run(["ffmpeg","-y",*in_av,*in_br,"-frames:v",str(n),"-filter_complex",
                f"{top};[0:v]{BOT}[bot];[top][bot]vstack=2[v]","-map","[v]",*enc,outp])
            cf.write(f"file '{outp}'\n")
    body = os.path.join(tmp,"body.mp4")
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",concat,"-c","copy",body])
    print(f"body: {int(probe_float(body,'format=duration')*FPS)} frames, {len(beats)} beats")

    # ── captions ──
    vparts = ["[0:v]"]; inputs=["-i",body]; idx=1
    badge = rel(base, plan.get("badge_png","")) if plan.get("badge_png") else ""
    fc=[]; prev="0:v"
    if badge and os.path.exists(badge):
        be = plan.get("badge_enable",[0,3.0]); inputs+=["-i",badge]
        bx,bypos = plan.get("badge_xy",[116,197])
        # Pre-scale the badge to a known canvas-relative width with SQUARE pixels so a PNG
        # authored at the wrong resolution / SAR can't composite distorted (the "#1 PICK out
        # of shape" bug). Opt-in via badge_w; absent -> legacy native-size overlay.
        bw_badge = plan.get("badge_w")
        if bw_badge:
            fc.append(f"[{idx}:v]scale={int(bw_badge)}:-1,setsar=1[bdgsrc]"); bsrc="bdgsrc"
        else:
            bsrc=f"{idx}:v"
        fc.append(f"[{prev}][{bsrc}]overlay={bx}:{bypos}:enable='between(t,{be[0]},{be[1]})'[v{idx}]")
        prev=f"v{idx}"; idx+=1
    if captions_on:
        tr_path = rel(base, plan["transcript"]) if plan.get("transcript") else None
        if tr_path and os.path.exists(tr_path):
            words = json.load(open(tr_path))["words"]
        else:
            aud = os.path.join(tmp,"voice.mp3")
            run(["ffmpeg","-y","-i",avatar,"-vn","-ac","1","-ar","16000","-b:a","96k",aud])
            words = groq_transcribe(aud, os.path.join(tmp,"transcript.json"))["words"]
        dur = probe_float(body,"format=duration")
        chunks = build_chunks(words, dur, cta_word=cap.get("cta_word","comment"),
                              cta_text=cap.get("cta_text",'Comment "SEO"'),
                              fixups=cap.get("fixups",{}),
                              cta_anchor=cap.get("cta_anchor"),
                              cta_tail_s=cap.get("cta_tail_s",2.5))
        capdir=os.path.join(tmp,"caps"); os.makedirs(capdir,exist_ok=True)
        pills=[]
        for i,c in enumerate(chunks):
            if c["end"]-c["start"]<0.08: continue
            png=os.path.join(capdir,f"c{i:03d}.png")
            pw,ph=render_pill(c["text"],png,FONT,PT,cap.get("padx",34),cap.get("pady",18),cap.get("radius",30))
            pills.append({"png":png,"x":(W-pw)//2,"y":SEAM_CY-ph//2,"start":c["start"],"end":c["end"]})
        for i in range(len(pills)-1): pills[i]["end"]=min(pills[i]["end"],pills[i+1]["start"])
        pills=[p for p in pills if p["end"]-p["start"]>0.05]
        for p in pills:
            inputs+=["-i",p["png"]]
            fc.append(f"[{prev}][{idx}:v]overlay={p['x']}:{p['y']}:enable='between(t,{round(p['start'],3)},{round(p['end'],3)})'[v{idx}]")
            prev=f"v{idx}"; idx+=1

    # ── audio: voice + SFX (typing bed + clicks on cuts) ──
    sfx = plan.get("sfx",{})
    typing = rel(base, sfx.get("typing", os.path.join(HERE,"assets","typing.wav")))
    click  = rel(base, sfx.get("click",  os.path.join(HERE,"assets","click.wav")))
    # SFX wavs are git-ignored; synthesize them on first run if missing
    if sfx.get("enabled", True) and (not os.path.exists(typing) or not os.path.exists(click)):
        mk = os.path.join(HERE, "make_sfx.py")
        if os.path.exists(mk):
            os.makedirs(os.path.dirname(typing) or ".", exist_ok=True)
            try: run(["python3", mk, os.path.dirname(typing) or "."])
            except SystemExit: pass
    # typing bed needs only the typing wav; clicks (one per cut) also need the click wav.
    use_sfx = sfx.get("enabled", True) and os.path.exists(typing)
    use_clicks = use_sfx and bool(cuts_ms) and os.path.exists(click)
    af=[]
    if use_sfx:
        ai=idx; inputs+=["-i",avatar,"-i",typing]
        af.append(f"[{ai}:a]volume=1.0[voice]")
        af.append(f"[{ai+1}:a]adelay=0|0,volume={sfx.get('typing_vol',0.13)}[typ]")
        labels=["[voice]","[typ]"]
        if use_clicks:
            inputs+=["-i",click]; ci=ai+2
            af.append(f"[{ci}:a]asplit={len(cuts_ms)}%s" % "".join(f"[c{i}]" for i in range(len(cuts_ms))))
            for i,ms in enumerate(cuts_ms):
                af.append(f"[c{i}]adelay={ms}|{ms},volume={sfx.get('click_vol',0.38)}[k{i}]"); labels.append(f"[k{i}]")
        af.append("".join(labels)+f"amix=inputs={len(labels)}:normalize=0:dropout_transition=0,alimiter=limit=0.95,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]")
        amap="[a]"
    else:
        ai=idx; inputs+=["-i",avatar]
        af.append(f"[{ai}:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]"); amap="[a]"

    if not fc:  # no overlays -> passthrough video
        fc=[f"[0:v]copy[vout]"]; prev="vout"
    filtergraph=";".join(fc+af)
    cmd=["ffmpeg","-y",*inputs,"-filter_complex",filtergraph,"-map",f"[{prev}]","-map",amap,
         "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-r",str(FPS),
         "-c:a","aac","-ar","48000","-b:a","192k","-movflags","+faststart","-shortest",out]
    run(cmd)
    print(f"RESULT: {json.dumps({'status':'succeeded','out':out,'duration':round(probe_float(out,'format=duration'),2),'beats':len(beats),'cuts':len(cuts_ms),'sfx':bool(use_sfx)})}")

if __name__ == "__main__":
    main()

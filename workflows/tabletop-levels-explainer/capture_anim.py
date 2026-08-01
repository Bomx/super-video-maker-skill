#!/usr/bin/env python3
"""Deterministically capture a paused-CSS-animation HTML page to an mp4 (frame-accurate).

Scrubs document.getAnimations().currentTime per frame so the diagram is reproducible.
Usage: capture_anim.py --html diagram.html --out flow_diagram.mp4 --dur 5.6 --fps 30
"""
import argparse, subprocess, tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("--html", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--dur", type=float, default=5.5)
ap.add_argument("--fps", type=int, default=30)
ap.add_argument("--w", type=int, default=720)
ap.add_argument("--h", type=int, default=1280)
ap.add_argument("--scale", type=int, default=2)
ap.add_argument("--selector", default="#stage")
a = ap.parse_args()

frames_dir = Path(tempfile.mkdtemp())
n = int(round(a.dur * a.fps))
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": a.w, "height": a.h}, device_scale_factor=a.scale)
    page.goto(Path(a.html).resolve().as_uri())
    page.wait_for_timeout(300)
    el = page.query_selector(a.selector)
    for i in range(n):
        page.evaluate("(t)=>{document.getAnimations().forEach(an=>{try{an.pause();an.currentTime=t;}catch(e){}});}", (i / a.fps) * 1000.0)
        el.screenshot(path=str(frames_dir / f"f_{i:04d}.png"))
    browser.close()

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(a.fps), "-i", str(frames_dir / "f_%04d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(a.fps), a.out], check=True)
print('RESULT: {"status":"succeeded","out":"%s","frames":%d}' % (a.out, n))

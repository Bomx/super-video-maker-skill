#!/usr/bin/env python3
"""Record coherent agent-operated browser footage on a VPS/Xvfb display.

This tool is designed for tutorial/news videos where the screen recording must
support narration. It preloads source pages, removes obvious ad clutter, then
records fast tab switching, scrolling, cursor movement, highlighted terms, and
large lower-third captions.

Run on a Linux VPS with Chrome, Xvfb, FFmpeg, and Playwright installed.
"""

import argparse
import json
import os
import signal
import subprocess
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


WIDTH = 1920
HEIGHT = 1080
FPS = 30


DEFAULT_SEGMENTS = [
    {
        "url": "https://searchengineland.com/google-updates-links-within-ai-overviews-ai-mode-476571",
        "tab": "AI links",
        "caption": "AI answers now show more links",
        "detail": "Inline citations and link previews mean content can still earn clicks.",
        "scroll": 520,
        "terms": ["five changes", "links and citations", "AI Mode and AI Overviews"],
        "hold": 14,
    },
    {
        "url": "https://crawlraven.com/blog/google-faq-rich-results-deprecated-may-2026",
        "tab": "FAQ rich results",
        "caption": "FAQ snippets are not the easy win",
        "detail": "Helpful answers still matter, but schema is no longer a shortcut.",
        "scroll": 360,
        "terms": ["FAQ rich results", "deprecated", "Search Console"],
        "hold": 12,
    },
    {
        "url": "https://developers.google.com/search/docs/fundamentals/creating-helpful-content",
        "tab": "Helpful content",
        "caption": "Original proof wins",
        "detail": "Examples, screenshots, data, and expertise make pages cite-worthy.",
        "scroll": 620,
        "terms": ["helpful", "reliable", "people-first", "expertise"],
        "hold": 14,
    },
]


def emit(payload):
    print("RESULT: " + json.dumps(payload), flush=True)


def start_xvfb(display):
    subprocess.run(["pkill", "-f", f"Xvfb {display}"], check=False)
    proc = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", f"{WIDTH}x{HEIGHT}x24", "+extension", "RANDR", "-ac", "-nolisten", "tcp"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    time.sleep(1.5)
    if proc.poll() is not None:
        stderr = proc.stderr.read().decode() if proc.stderr else ""
        raise RuntimeError(f"Xvfb failed: {stderr}")
    os.environ["DISPLAY"] = display
    subprocess.run(["xsetroot", "-cursor_name", "left_ptr"], check=False, env=os.environ)
    return proc


def start_ffmpeg(display, output_video):
    output_video.parent.mkdir(parents=True, exist_ok=True)
    if output_video.exists():
        output_video.unlink()
    cmd = [
        "ffmpeg", "-y",
        "-f", "x11grab",
        "-video_size", f"{WIDTH}x{HEIGHT}",
        "-framerate", str(FPS),
        "-draw_mouse", "1",
        "-i", display,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        str(output_video),
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=os.environ)
    time.sleep(1)
    if proc.poll() is not None:
        stderr = proc.stderr.read().decode() if proc.stderr else ""
        raise RuntimeError(f"FFmpeg failed: {stderr}")
    return proc


def clean_page(page):
    page.evaluate(
        """
        () => {
          const bad = ['advertisement', 'sponsored', 'adchoices', 'newsletter'];
          for (const el of Array.from(document.querySelectorAll('iframe, aside'))) el.remove();
          for (const el of Array.from(document.querySelectorAll('body *'))) {
            const text = (el.innerText || '').slice(0, 240).toLowerCase();
            const klass = `${el.id || ''} ${el.className || ''}`.toLowerCase();
            const rect = el.getBoundingClientRect();
            if (
              klass.includes('advert') || klass.includes('sponsor') || klass.includes('dfp') ||
              bad.some(b => text.includes(b)) ||
              (rect.top < 360 && rect.width > 900 && rect.height > 160 && bad.some(b => text.includes(b)))
            ) el.remove();
          }
          document.documentElement.style.scrollBehavior = 'smooth';
        }
        """
    )


def overlay(page, caption, detail):
    page.evaluate(
        """
        ({caption, detail}) => {
          const old = document.getElementById('agent-caption-overlay');
          if (old) old.remove();
          const box = document.createElement('div');
          box.id = 'agent-caption-overlay';
          box.style.cssText = `
            position: fixed; left: 28px; bottom: 28px; z-index: 2147483647;
            width: 720px; padding: 18px 22px; border-radius: 18px;
            border: 4px solid #ff6b2c; background: rgba(6,10,20,.90);
            color: white; font-family: Inter, Arial, sans-serif;
            box-shadow: 0 18px 70px rgba(0,0,0,.35);
          `;
          box.innerHTML = `
            <div style="font-size:42px;line-height:1;font-weight:1000;letter-spacing:-1px;text-transform:uppercase;">${caption}</div>
            <div style="font-size:19px;line-height:1.3;color:#dbeafe;margin-top:10px;">${detail}</div>
          `;
          document.body.appendChild(box);
        }
        """,
        {"caption": caption, "detail": detail},
    )


def highlight_terms(page, terms):
    page.evaluate(
        """
        (terms) => {
          const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          const nodes = [];
          while (walker.nextNode()) nodes.push(walker.currentNode);
          for (const term of terms) {
            const lower = term.toLowerCase();
            for (const node of nodes) {
              const text = node.nodeValue || '';
              const idx = text.toLowerCase().indexOf(lower);
              if (idx < 0 || !node.parentElement || node.parentElement.closest('#agent-caption-overlay')) continue;
              const wrap = document.createElement('span');
              wrap.innerHTML = `${text.slice(0, idx)}<mark style="background:#ffef5a;color:#050505;padding:3px 6px;border-radius:5px;font-weight:700;">${text.slice(idx, idx + term.length)}</mark>${text.slice(idx + term.length)}`;
              node.parentElement.replaceChild(wrap, node);
              break;
            }
          }
        }
        """,
        terms,
    )


def load_segments(path):
    if not path:
        return DEFAULT_SEGMENTS
    data = json.loads(Path(path).read_text())
    return data["segments"] if isinstance(data, dict) and "segments" in data else data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--segments-json", help="JSON list or {'segments': [...]} file")
    parser.add_argument("--output", default="screen_recordings/agent_browser_recording.mp4")
    parser.add_argument("--events", default="")
    parser.add_argument("--display", default=":97")
    parser.add_argument("--chrome", default="/usr/bin/google-chrome")
    args = parser.parse_args()

    output_video = Path(args.output).resolve()
    events_path = Path(args.events).resolve() if args.events else output_video.with_name(output_video.stem + "_events.json")
    segments = load_segments(args.segments_json)
    events = {"started_at": time.time(), "output_video": str(output_video), "events": [], "segments": segments}
    xvfb = ffmpeg_proc = browser = None

    try:
        xvfb = start_xvfb(args.display)
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=args.chrome,
                headless=False,
                args=["--no-sandbox", "--disable-dev-shm-usage", f"--window-size={WIDTH},{HEIGHT}", "--start-maximized", "--disable-notifications"],
                env={**os.environ, "DISPLAY": args.display},
            )
            context = browser.new_context(viewport={"width": WIDTH, "height": HEIGHT})
            pages = []
            for segment in segments:
                page = context.new_page()
                print(f"Preload: {segment.get('tab') or segment['url']}")
                page.goto(segment["url"], wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(1200)
                clean_page(page)
                page.evaluate(f"window.scrollTo(0, {int(segment.get('scroll', 0))})")
                highlight_terms(page, segment.get("terms", []))
                overlay(page, segment.get("caption", ""), segment.get("detail", ""))
                pages.append(page)

            pages[0].bring_to_front()
            time.sleep(0.8)
            events["started_at"] = time.time()
            ffmpeg_proc = start_ffmpeg(args.display, output_video)

            for page, segment in zip(pages, segments):
                page.bring_to_front()
                ts = round(time.time() - events["started_at"], 2)
                events["events"].append({"timestamp": ts, "type": "tab", "label": segment.get("tab", segment["url"])})
                clean_page(page)
                overlay(page, segment.get("caption", ""), segment.get("detail", ""))
                highlight_terms(page, segment.get("terms", []))
                page.mouse.move(900, 500, steps=22)
                page.wait_for_timeout(900)
                page.mouse.wheel(0, 380)
                page.wait_for_timeout(1600)
                page.mouse.move(640, 420, steps=18)
                page.wait_for_timeout(800)
                page.mouse.wheel(0, -180)
                page.wait_for_timeout(max(2000, int((float(segment.get("hold", 10)) - 4.0) * 1000)))

            context.close()
            browser.close()
            browser = None
    finally:
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text(json.dumps(events, indent=2))
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        if ffmpeg_proc:
            ffmpeg_proc.send_signal(signal.SIGINT)
            try:
                ffmpeg_proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                ffmpeg_proc.kill()
        if xvfb:
            xvfb.terminate()
            try:
                xvfb.wait(timeout=5)
            except subprocess.TimeoutExpired:
                xvfb.kill()

    emit({"status": "succeeded", "local_path": str(output_video), "events_path": str(events_path), "stage": "agent_browser_recording"})


if __name__ == "__main__":
    main()

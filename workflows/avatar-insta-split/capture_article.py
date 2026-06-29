#!/usr/bin/env python3
"""Capture a tall article screenshot for an avatar-insta-split SCROLL reel.

Produces a single PNG rendered at the canvas width (1080px by default, via a 540px mobile
viewport at device_scale_factor=2), starting at the very TOP so the headline (H1) is
included, and writes a sidecar JSON of section-heading y-offsets (in the SAME px space as
the PNG) so you can author per-beat scroll_from/scroll_to directly.

Chrome wraps full-page rasters >16384px (content repeats from the top), so the page is
captured in <=3500-CSS-px segments and stitched.

Usage:
    python3 capture_article.py "https://example.com/blog/best-x" article.png
"""
import json, sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

SEG_CSS = 3500           # CSS px per segment (raster 7000px < 16384 limit)
DSF = 2                  # device scale factor -> raster width = viewport*DSF = 1080


def settle(page):
    last = -1
    for _ in range(60):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(120)
        cur = page.evaluate("window.scrollY")
        if cur == last:
            break
        last = cur
    page.wait_for_timeout(400)
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(400)


def capture(url, out_png):
    out_png = Path(out_png)
    sections_path = out_png.with_suffix(".sections.json")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        ctx = browser.new_context(
            viewport={"width": 540, "height": 960}, device_scale_factor=DSF,
            is_mobile=True, has_touch=True,
            user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"),
        )
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle", timeout=60000)
        settle(page)

        css_h = page.evaluate("document.documentElement.scrollHeight")
        # heading y-offsets (CSS*DSF -> raster px == PNG px == build_reel scroll px)
        headings = page.evaluate(
            """() => [...document.querySelectorAll('h1,h2,h3')].map(e => ({
                tag: e.tagName, text: (e.textContent||'').trim().slice(0,80),
                y: Math.round(e.getBoundingClientRect().top + window.scrollY)
            }))""")
        for h in headings:
            h["y_px"] = h["y"] * DSF

        segs, y, i = [], 0, 0
        while y < css_h:
            h = min(SEG_CSS, css_h - y)
            path = out_png.parent / f"_seg_{i:02d}.png"
            page.screenshot(path=str(path), full_page=True, clip={"x": 0, "y": y, "width": 540, "height": h})
            segs.append(path); y += h; i += 1

        if not segs:
            browser.close()
            print("RESULT:", json.dumps({"status": "failed",
                  "error": f"page has no scrollable height (css_h={css_h}); blank/paywalled/JS-only?"}))
            raise SystemExit(1)

        parts = [Image.open(s) for s in segs]
        total_h = sum(im.height for im in parts)
        out = Image.new("RGB", (parts[0].width, total_h), "white")
        yy = 0
        for im in parts:
            out.paste(im, (0, yy)); yy += im.height
        out.save(out_png)
        for s in segs:
            s.unlink()
        browser.close()

    sections_path.write_text(json.dumps({"width": parts[0].width, "height": total_h,
                                         "headings": headings}, indent=2))
    print("RESULT:", json.dumps({"status": "succeeded", "png": str(out_png),
                                 "sections": str(sections_path),
                                 "size": [parts[0].width, total_h], "headings": len(headings)}))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit("usage: capture_article.py <url> <out.png>")
    capture(sys.argv[1], sys.argv[2])

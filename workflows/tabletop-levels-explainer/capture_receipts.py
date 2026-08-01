#!/usr/bin/env python3
"""Capture real screenshot 'receipts' for proof beats (headless system Chrome).

Env: SVM_JOB. Reads receipts.json = [{"name":"agi_wiki","url":"https://...","scroll":0}, ...]
Writes assets/receipts/<name>.png. Falls back to argv JSON if receipts.json is absent.
"""
import json, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

JOB = Path(os.environ["SVM_JOB"])
OUT = JOB / "assets/receipts"; OUT.mkdir(parents=True, exist_ok=True)
rp = JOB / "receipts.json"
TARGETS = json.loads(rp.read_text()) if rp.exists() else json.loads(sys.argv[1] if len(sys.argv) > 1 else "[]")

done = []
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    for t in TARGETS:
        try:
            pg = b.new_page(viewport={"width": 1120, "height": 1640}, device_scale_factor=2)
            pg.goto(t["url"], wait_until="domcontentloaded", timeout=45000)
            pg.wait_for_timeout(2500)
            if t.get("scroll"):
                pg.evaluate("(y)=>window.scrollTo(0,y)", t["scroll"]); pg.wait_for_timeout(600)
            pg.screenshot(path=str(OUT / f"{t['name']}.png"))
            done.append(t["name"]); print(f"[receipt] {t['name']} ok", file=sys.stderr); pg.close()
        except Exception as e:
            print(f"[receipt] {t['name']} FAIL {str(e)[:120]}", file=sys.stderr)
    b.close()
print("RESULT: " + json.dumps({"status": "succeeded", "receipts": done}))

#!/usr/bin/env python3
"""Build minimalist word-locked captions (small, clean, lower-third) as an ASS file.

Env: SVM_JOB. Reads analysis/presenter_timing.json + overlay_schedule.json (optional:
keyword_captions_color, phrase_captions). Writes assets/captions.ass.
"""
import json, os
from pathlib import Path

JOB = Path(os.environ["SVM_JOB"])
timing = json.loads((JOB / "analysis/presenter_timing.json").read_text())
sched = {}
sp = JOB / "overlay_schedule.json"
if sp.exists():
    sched = json.loads(sp.read_text())
words = timing["words"]
colors = sched.get("keyword_captions_color", {})

def ass_t(s):
    h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
    return f"{h}:{m:02d}:{sec:05.2f}"

phrases, cur = [], []
for w in words:
    cur.append(w)
    if len(cur) >= 3 or w["w"].endswith((".", "?", "!", ",")):
        phrases.append(cur); cur = []
if cur: phrases.append(cur)

HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Arial,46,&H00FFFFFF,&H00FFFFFF,&H00202020,&H64000000,-1,0,0,0,100,100,0,0,1,2,1,2,90,90,330,1

[Events]
Format: Layer, Start, End, Style, MarginL, MarginR, MarginV, Effect, Text
"""

def hex_to_ass(h):
    h = h.lstrip("#"); r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}".upper()

lines = []
for i, ph in enumerate(phrases):
    t0 = ph[0]["start"]
    t1 = phrases[i + 1][0]["start"] if i + 1 < len(phrases) else ph[-1]["end"] + 0.3
    t1 = min(t1, ph[-1]["end"] + 0.6)
    txt = " ".join(w["w"] for w in ph).strip()
    col = next((colors[w["w"]] for w in ph if w["w"] in colors), None)
    pre = f"{{\\c{hex_to_ass(col)}}}" if col else ""
    lines.append(f"Dialogue: 0,{ass_t(t0)},{ass_t(t1)},Cap,90,90,330,,{pre}{txt}")

for pc in sched.get("phrase_captions", []):
    pre = f"{{\\c{hex_to_ass(pc['color'])}}}" if pc.get("color") else ""
    lines.append(f"Dialogue: 1,{ass_t(pc['t0'])},{ass_t(pc['t1'])},Cap,90,90,560,,{pre}{pc['text']}")

(JOB / "assets/captions.ass").write_text(HEADER + "\n".join(lines) + "\n")
print("RESULT: " + json.dumps({"status": "succeeded", "phrases": len(phrases)}))

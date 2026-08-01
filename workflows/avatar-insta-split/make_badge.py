#!/usr/bin/env python3
"""Render the '#1 PICK' hook badge in-pipeline, at exact canvas DPI with SQUARE pixels.

This fixes two things at once:
  * shape: the card is generated at a known width with a 1:1 pixel aspect, so it can never
    composite "out of shape" the way a hand-made PNG of the wrong resolution/SAR did;
  * language: the label is localized (the badge text used to be baked into an English PNG).

Usage:
    python3 make_badge.py --brand "De Vries Geveltechniek" --language Dutch --out badge.png
    python3 make_badge.py --brand "Acme" --label "#1 PICK" --width 848 --out badge.png
"""
import argparse
from PIL import Image, ImageDraw, ImageFont

# default "#1 <pick word>" per language (override with --label)
LABELS = {
    "en": "#1 PICK", "nl": "#1 KEUZE", "fr": "#1 CHOIX", "es": "#1 ELECCIÓN",
    "de": "#1 WAHL", "it": "#1 SCELTA", "pt": "#1 ESCOLHA", "pl": "#1 WYBÓR",
    "sv": "#1 VAL", "da": "#1 VALG", "no": "#1 VALG",
}
LANG_ALIAS = {"english": "en", "dutch": "nl", "nederlands": "nl", "flemish": "nl",
              "french": "fr", "spanish": "es", "german": "de", "italian": "it",
              "portuguese": "pt", "polish": "pl", "swedish": "sv", "danish": "da", "norwegian": "no"}

SUP = "/System/Library/Fonts/Supplemental"


def _font(sz, bold=True):
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    try:
        return ImageFont.truetype(f"{SUP}/{name}", sz)
    except Exception:
        return ImageFont.load_default()


def label_for(language: str) -> str:
    s = (language or "en").strip().lower()
    iso = s if len(s) == 2 else LANG_ALIAS.get(s, "en")
    return LABELS.get(iso, LABELS["en"])


def render_badge(brand: str, out: str, label: str = None, language: str = "en",
                 width: int = 848, accent=(212, 175, 55), bg=(20, 20, 22), fg=(245, 245, 245)):
    label = label or label_for(language)
    pad = int(width * 0.06)
    label_pt = int(width * 0.085)
    brand_pt = int(width * 0.105)
    lf, bf = _font(label_pt), _font(brand_pt)
    scratch = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    def wrap(text, font, max_w):
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if scratch.textlength(t, font=font) <= max_w or not cur:
                cur = t
            else:
                lines.append(cur); cur = w
        if cur:
            lines.append(cur)
        return lines

    inner = width - 2 * pad
    brand_lines = wrap(brand, bf, inner)
    lh_label = label_pt + int(label_pt * 0.35)
    lh_brand = brand_pt + int(brand_pt * 0.28)
    height = pad + lh_label + int(label_pt * 0.25) + lh_brand * len(brand_lines) + pad

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(width * 0.065)
    d.rounded_rectangle([0, 0, width - 1, height - 1], radius=r, fill=bg + (240,))
    d.rounded_rectangle([6, 6, width - 7, height - 7], radius=r - 4, outline=accent + (255,), width=max(3, width // 280))
    y = pad
    d.text((pad, y), label, font=lf, fill=accent)
    y += lh_label + int(label_pt * 0.25)
    for ln in brand_lines:
        d.text((pad, y), ln, font=bf, fill=fg)
        y += lh_brand
    img.save(out)
    return {"out": out, "width": width, "height": height, "label": label, "brand": brand}


if __name__ == "__main__":
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("--brand", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default=None, help="override the localized '#1 ...' label")
    ap.add_argument("--language", default="en")
    ap.add_argument("--width", type=int, default=848)
    a = ap.parse_args()
    print("RESULT:", json.dumps(render_badge(a.brand, a.out, a.label, a.language, a.width)))

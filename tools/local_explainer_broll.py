import math
import os
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter


JOB_DIR = Path.cwd()
OUT_DIR = JOB_DIR / "output_videos" / "local_broll"
FPS = 30
W, H = 1920, 1080
DURATION = 7
FRAMES = FPS * DURATION


def font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


FONT_BIG = font(88, True)
FONT_MED = font(42, True)
FONT_SMALL = font(30, False)


def lerp(a, b, t):
    return a + (b - a) * t


def background(t, c1=(7, 12, 28), c2=(22, 32, 58)):
    img = Image.new("RGB", (W, H), c1)
    px = img.load()
    for y in range(H):
        k = y / H
        r = int(lerp(c1[0], c2[0], k))
        g = int(lerp(c1[1], c2[1], k))
        b = int(lerp(c1[2], c2[2], k))
        for x in range(W):
            px[x, y] = (r, g, b)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for i, (cx, cy, col) in enumerate([
        (int(W * (0.18 + 0.03 * math.sin(t * 4))), int(H * 0.25), (255, 107, 44)),
        (int(W * 0.78), int(H * (0.65 + 0.04 * math.cos(t * 3))), (94, 234, 212)),
    ]):
        for r in range(360, 0, -8):
            alpha = int(26 * (r / 360))
            gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*col, alpha))
    return Image.alpha_composite(img.convert("RGBA"), glow)


def rounded(draw, xy, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def draw_title(draw, title, subtitle):
    draw.text((72, 62), title, font=FONT_BIG, fill=(255, 255, 255))
    draw.text((78, 168), subtitle, font=FONT_SMALL, fill=(210, 225, 255))


def scene_ai_links(frame):
    t = frame / FRAMES
    img = background(t)
    d = ImageDraw.Draw(img)
    draw_title(d, "AI ANSWERS NEED SOURCES", "The winner is the page AI can confidently cite.")
    site_x = int(200 + 80 * math.sin(t * math.pi))
    site_y = 620
    rounded(d, (site_x, site_y, site_x + 420, site_y + 220), 28, (20, 35, 65, 245), (255, 107, 44), 5)
    d.text((site_x + 38, site_y + 42), "Original Website", font=FONT_MED, fill=(255, 255, 255))
    for i in range(4):
        d.rounded_rectangle((site_x + 42, site_y + 105 + i * 25, site_x + 360 - i * 35, site_y + 121 + i * 25), radius=8, fill=(85, 110, 150, 255))
    panel_x, panel_y = 980, 285
    rounded(d, (panel_x, panel_y, panel_x + 660, panel_y + 420), 34, (245, 248, 255, 245), (94, 234, 212), 5)
    d.text((panel_x + 48, panel_y + 42), "AI Answer", font=FONT_MED, fill=(10, 18, 32))
    for i in range(6):
        y = panel_y + 115 + i * 42
        d.rounded_rectangle((panel_x + 48, y, panel_x + 560 - (i % 3) * 60, y + 18), radius=8, fill=(45, 64, 96, 255))
    for i in range(7):
        p = min(1, max(0, t * 1.4 - i * 0.08))
        sx = site_x + 420
        sy = site_y + 55 + i * 22
        ex = panel_x + 35
        ey = panel_y + 115 + i * 40
        mx = int(lerp(sx, ex, p))
        my = int(lerp(sy, ey, p))
        d.line((sx, sy, mx, my), fill=(255, 221, 87, 220), width=5)
        d.ellipse((mx - 8, my - 8, mx + 8, my + 8), fill=(255, 221, 87, 255))
    return img


def scene_faq(frame):
    t = frame / FRAMES
    img = background(t, (10, 11, 24), (39, 23, 56))
    d = ImageDraw.Draw(img)
    draw_title(d, "THE OLD SHORTCUT DISAPPEARS", "FAQ schema alone is not a strategy anymore.")
    for i in range(5):
        x = 170 + i * 128
        y = int(665 - i * 70 - 90 * t)
        alpha = int(255 * max(0, 1 - t * 1.2))
        card = Image.new("RGBA", (260, 110), (255, 216, 88, alpha))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((0, 0, 260, 110), radius=22, fill=(255, 216, 88, alpha), outline=(255, 255, 255, alpha), width=3)
        cd.text((32, 30), "FAQ", font=FONT_MED, fill=(20, 20, 30, alpha))
        img.alpha_composite(card, (x, y))
    lab_x = int(930 - 70 * (1 - min(1, t * 1.5)))
    rounded(d, (lab_x, 350, lab_x + 760, 430), 20, (255, 255, 255, 245), None, 1)
    d.text((lab_x + 40, 370), "HELPFUL CONTENT LAB", font=FONT_MED, fill=(13, 24, 38))
    items = ["screenshots", "original data", "expert opinion", "real examples"]
    for i, item in enumerate(items):
        y = 480 + i * 80
        rounded(d, (lab_x + 30, y, lab_x + 610, y + 48), 15, (31, 48, 78, 240), (94, 234, 212), 2)
        d.text((lab_x + 58, y + 9), item.upper(), font=FONT_SMALL, fill=(255, 255, 255))
        d.ellipse((lab_x + 635, y + 8, lab_x + 675, y + 48), fill=(34, 197, 94, 255))
    return img


def scene_authority(frame):
    t = frame / FRAMES
    img = background(t, (5, 10, 24), (18, 36, 58))
    d = ImageDraw.Draw(img)
    draw_title(d, "BECOME THE CITED SOURCE", "AI search rewards pages with proof, expertise, and trust.")
    generic = (250, 530)
    strong = (1120, 520)
    rounded(d, (generic[0], generic[1], generic[0] + 320, generic[1] + 190), 24, (95, 105, 125, 190), (150, 150, 160), 3)
    d.text((generic[0] + 52, generic[1] + 70), "Generic page", font=FONT_SMALL, fill=(230, 230, 235))
    rounded(d, (strong[0], strong[1], strong[0] + 400, strong[1] + 230), 28, (18, 38, 72, 245), (255, 107, 44), 5)
    d.text((strong[0] + 52, strong[1] + 72), "Authority page", font=FONT_MED, fill=(255, 255, 255))
    center = (strong[0] + 200, strong[1] + 115)
    for i, label in enumerate(["DATA", "PROOF", "EXPERT", "SCREENSHOT", "CITATION"]):
        angle = t * 2 * math.pi + i * 2 * math.pi / 5
        x = int(center[0] + math.cos(angle) * 330)
        y = int(center[1] + math.sin(angle) * 210)
        d.line((center[0], center[1], x, y), fill=(94, 234, 212, 160), width=3)
        d.ellipse((x - 52, y - 52, x + 52, y + 52), fill=(255, 107, 44, 235))
        d.text((x - 42, y - 12), label, font=font(20, True), fill=(255, 255, 255))
    beam_p = min(1, t * 1.4)
    d.line((820, 330, int(lerp(820, strong[0] + 80, beam_p)), int(lerp(330, strong[1] + 60, beam_p))), fill=(255, 221, 87, 255), width=8)
    d.text((720, 270), "AI CITES", font=FONT_MED, fill=(255, 221, 87))
    return img


SCENES = [
    ("broll_ai_links_citation_network_local.mp4", scene_ai_links),
    ("broll_faq_shortcut_disappears_local.mp4", scene_faq),
    ("broll_authority_constellation_local.mp4", scene_authority),
]


def render_scene(name, fn):
    temp_dir = OUT_DIR / name.replace(".mp4", "_frames")
    temp_dir.mkdir(parents=True, exist_ok=True)
    for frame in range(FRAMES):
        img = fn(frame)
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=115, threshold=3))
        img.convert("RGB").save(temp_dir / f"frame_{frame:05d}.jpg", quality=92)
    out = OUT_DIR / name
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(temp_dir / "frame_%05d.jpg"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        "-preset", "medium",
        str(out),
    ]
    subprocess.run(cmd, check=True)
    for p in temp_dir.glob("*.jpg"):
        p.unlink()
    temp_dir.rmdir()
    print(out)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, fn in SCENES:
        render_scene(name, fn)


if __name__ == "__main__":
    main()

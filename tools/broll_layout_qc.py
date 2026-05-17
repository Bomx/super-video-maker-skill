#!/usr/bin/env python3
"""Create b-roll layout review frames/contact sheets with safe-zone guides.

This is not a replacement for human/vision taste review. It is the gate that
makes the review easy and consistent:

1. Extract representative frames from each generated b-roll clip or still.
2. Overlay layout guides:
   - outer safe margin,
   - top-right avatar PiP reserved zone,
   - bottom caption band,
   - center composition crosshair.
3. Build a contact sheet for fast visual inspection.
4. Emit a RESULT JSON with artifacts and a checklist.

Usage:
    python3 broll_layout_qc.py clip1.mp4 clip2.png --job-dir tmp/video_jobs/foo

The agent should then open/read the contact sheet images and decide:
pass / crop-edit / re-render / replace.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
DEFAULT_SAFE_MARGIN = 90
DEFAULT_CAPTION_BAND = 170
DEFAULT_PIP = (1378, 50, 492, 276)  # x, y, w, h

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm"}


def emit(payload: dict) -> None:
    print("RESULT: " + json.dumps(payload), flush=True)


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def probe_duration(path: Path) -> float:
    proc = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path),
    ])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ffprobe failed for {path}")
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 0.0


def font(size: int = 28) -> ImageFont.ImageFont:
    for path in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
    ]:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def fit_frame(src: Image.Image, size: tuple[int, int] = (W, H)) -> Image.Image:
    tw, th = size
    img = src.convert("RGB")
    scale = max(tw / img.width, th / img.height)
    nw, nh = int(img.width * scale), int(img.height * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 2
    return img.crop((x, y, x + tw, y + th))


def extract_video_frame(video: Path, timestamp: float, output: Path) -> Path:
    proc = run([
        "ffmpeg", "-y", "-ss", f"{timestamp:.3f}", "-i", str(video),
        "-frames:v", "1", "-update", "1", "-q:v", "2", str(output),
    ])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"ffmpeg frame extraction failed for {video}")
    return output


def draw_guides(
    image: Image.Image,
    label: str,
    safe_margin: int,
    caption_band: int,
    pip: tuple[int, int, int, int],
) -> Image.Image:
    img = image.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    fnt = font(26)

    # Safe margin.
    d.rectangle(
        (safe_margin, safe_margin, W - safe_margin, H - safe_margin),
        outline=(94, 234, 212, 210),
        width=4,
    )
    d.text((safe_margin + 10, safe_margin + 10), "safe area", font=fnt, fill=(94, 234, 212, 230))

    # Caption band.
    y0 = H - caption_band
    d.rectangle((0, y0, W, H), fill=(255, 230, 0, 45), outline=(255, 230, 0, 210), width=4)
    d.text((30, y0 + 16), "caption band: avoid key text/faces here", font=fnt, fill=(255, 230, 0, 255))

    # PiP reserved zone.
    px, py, pw, ph = pip
    d.rounded_rectangle(
        (px, py, px + pw, py + ph),
        radius=26,
        fill=(255, 107, 44, 50),
        outline=(255, 107, 44, 230),
        width=5,
    )
    d.text((px + 16, py + 16), "avatar PiP reserved", font=fnt, fill=(255, 107, 44, 255))

    # Center crosshair / thirds-ish anchors.
    d.line((W // 2, safe_margin, W // 2, H - safe_margin), fill=(255, 255, 255, 105), width=2)
    d.line((safe_margin, H // 2, W - safe_margin, H // 2), fill=(255, 255, 255, 105), width=2)

    # Label.
    d.rounded_rectangle((24, 24, 780, 78), radius=18, fill=(10, 18, 40, 235))
    d.text((48, 38), label[:86], font=fnt, fill=(255, 255, 255, 255))

    return Image.alpha_composite(img, overlay).convert("RGB")


def sample_times(duration: float, count: int) -> list[float]:
    if duration <= 0:
        return [0.0]
    if count <= 1:
        return [min(duration * 0.5, max(0, duration - 0.05))]
    # Avoid exact first/last frames.
    return [duration * (i + 1) / (count + 1) for i in range(count)]


def make_contact_sheet(images: list[Path], output: Path, thumb_width: int = 480) -> Path:
    thumbs: list[Image.Image] = []
    for path in images:
        im = Image.open(path).convert("RGB")
        h = int(im.height * (thumb_width / im.width))
        thumbs.append(im.resize((thumb_width, h), Image.Resampling.LANCZOS))

    if not thumbs:
        raise ValueError("No images for contact sheet")

    cols = min(3, len(thumbs))
    rows = math.ceil(len(thumbs) / cols)
    gap = 18
    cell_h = max(t.height for t in thumbs)
    sheet = Image.new("RGB", (cols * thumb_width + gap * (cols + 1), rows * cell_h + gap * (rows + 1)), (18, 24, 38))
    for idx, thumb in enumerate(thumbs):
        col = idx % cols
        row = idx // cols
        x = gap + col * (thumb_width + gap)
        y = gap + row * (cell_h + gap)
        sheet.paste(thumb, (x, y))
    sheet.save(output, quality=92)
    return output


def review_asset(
    path: Path,
    out_dir: Path,
    frames_per_video: int,
    safe_margin: int,
    caption_band: int,
    pip: tuple[int, int, int, int],
) -> dict:
    stem = path.stem
    raw_dir = out_dir / "raw"
    guide_dir = out_dir / "guided"
    raw_dir.mkdir(parents=True, exist_ok=True)
    guide_dir.mkdir(parents=True, exist_ok=True)

    guided_paths: list[Path] = []
    duration = None

    if path.suffix.lower() in VIDEO_EXTS:
        duration = probe_duration(path)
        for idx, ts in enumerate(sample_times(duration, frames_per_video), start=1):
            raw = raw_dir / f"{stem}_t{idx}_{ts:.2f}.jpg"
            extract_video_frame(path, ts, raw)
            frame = fit_frame(Image.open(raw))
            guided = draw_guides(frame, f"{path.name} @ {ts:.2f}s", safe_margin, caption_band, pip)
            guided_path = guide_dir / f"{stem}_t{idx}_{ts:.2f}_guided.jpg"
            guided.save(guided_path, quality=92)
            guided_paths.append(guided_path)
    elif path.suffix.lower() in IMAGE_EXTS:
        frame = fit_frame(Image.open(path))
        guided = draw_guides(frame, path.name, safe_margin, caption_band, pip)
        guided_path = guide_dir / f"{stem}_guided.jpg"
        guided.save(guided_path, quality=92)
        guided_paths.append(guided_path)
    else:
        raise ValueError(f"Unsupported asset type: {path}")

    return {
        "asset": str(path),
        "duration_seconds": round(duration, 3) if duration is not None else None,
        "guided_frames": [str(p) for p in guided_paths],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("assets", nargs="+", help="Video/image b-roll assets to review")
    parser.add_argument("--job-dir", default="", help="Job directory for output. Defaults to common parent.")
    parser.add_argument("--output-dir", default="", help="Explicit output directory")
    parser.add_argument("--frames-per-video", type=int, default=3)
    parser.add_argument("--safe-margin", type=int, default=DEFAULT_SAFE_MARGIN)
    parser.add_argument("--caption-band", type=int, default=DEFAULT_CAPTION_BAND)
    parser.add_argument("--pip", default="1378,50,492,276", help="x,y,w,h for PiP reserved zone")
    args = parser.parse_args()

    try:
        assets = [Path(p).expanduser().resolve() for p in args.assets]
        missing = [str(p) for p in assets if not p.exists()]
        if missing:
            emit({"status": "failed", "error": "Missing assets", "missing": missing})
            sys.exit(2)

        pip_parts = tuple(int(v.strip()) for v in args.pip.split(","))
        if len(pip_parts) != 4:
            raise ValueError("--pip must be x,y,w,h")

        if args.output_dir:
            out_dir = Path(args.output_dir).expanduser().resolve()
        elif args.job_dir:
            out_dir = Path(args.job_dir).expanduser().resolve() / "layout_qc"
        else:
            common = Path(assets[0]).parent
            out_dir = common / "layout_qc"
        out_dir.mkdir(parents=True, exist_ok=True)

        reviews = [
            review_asset(
                path=p,
                out_dir=out_dir,
                frames_per_video=args.frames_per_video,
                safe_margin=args.safe_margin,
                caption_band=args.caption_band,
                pip=pip_parts,  # type: ignore[arg-type]
            )
            for p in assets
        ]

        all_guided = [Path(frame) for review in reviews for frame in review["guided_frames"]]
        contact_sheet = make_contact_sheet(all_guided, out_dir / "broll_layout_contact_sheet.jpg")

        checklist = [
            "Key subject is not hidden under the top-right avatar PiP box.",
            "Important text/faces are not in the bottom caption band.",
            "Main subject has breathing room inside the safe area.",
            "No awkward edge tangents, clipped UI, or cramped typography.",
            "Every shot has one editorial job: proof, mechanism, consequence, action, or transition.",
            "If spacing is off: crop/reframe first, then edit layout, then re-render/replace.",
        ]

        report = {
            "status": "succeeded",
            "output_dir": str(out_dir),
            "contact_sheet": str(contact_sheet),
            "reviews": reviews,
            "checklist": checklist,
            "next_action": "Open/read the contact sheet frames, mark each asset pass/crop-edit/re-render/replace before final composition.",
        }
        (out_dir / "broll_layout_qc_report.json").write_text(json.dumps(report, indent=2))
        emit(report)
    except Exception as exc:
        emit({"status": "failed", "error": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()

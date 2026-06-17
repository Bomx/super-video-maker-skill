#!/usr/bin/env python3
"""Quality gate for reference-driven UGC/video ads.

The gate combines machine checks with review artifacts:

- one-frame-per-second candidate sampling,
- reference-vs-candidate timing/contact sheets,
- dense contact sheets around risky UI/phone/CTA/face windows,
- transcript and voice-speed checks,
- simple visual heuristics for blank/low-detail screen risk.

It intentionally produces inspectable artifacts instead of a single opaque
score. The goal is to catch issues before an ad is handed to the user.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont


RISK_KEYWORDS = {
    "phone",
    "screen",
    "website",
    "site",
    "ui",
    "dashboard",
    "cta",
    "price",
    "trial",
    "free",
    "start",
    "connect",
    "logo",
    "checkout",
    "text",
    "caption",
    "face",
    "hand",
    "hands",
}


@dataclass
class FrameSample:
    timestamp: float
    path: Path
    brightness: float
    contrast: float
    edge_density: float
    white_fraction: float


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return result.stdout


def require_binary(name: str) -> None:
    if not shutil.which(name):
        raise RuntimeError(f"Required binary not found on PATH: {name}")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT_TITLE = font(26, True)
FONT_BODY = font(20, False)
FONT_SMALL = font(16, False)


def probe_duration(path: Path) -> float:
    data = json.loads(
        run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(path),
            ]
        )
    )
    return float(data["format"]["duration"])


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def transcript_text(summary: dict[str, Any]) -> str:
    if summary.get("full_text"):
        return str(summary["full_text"])
    return " ".join(str(segment.get("text", "")) for segment in summary.get("segments") or [])


def word_count_from_summary(summary: dict[str, Any]) -> int:
    if summary.get("word_count"):
        return int(summary["word_count"])
    return len(re.findall(r"\b[\w']+\b", transcript_text(summary)))


def speech_span(summary: dict[str, Any], fallback_duration: float) -> float:
    segments = summary.get("segments") or []
    if not segments:
        return fallback_duration
    starts = [float(s.get("start", 0.0)) for s in segments]
    ends = [float(s.get("end", 0.0)) for s in segments]
    return max(0.01, max(ends) - min(starts))


def resolve_path(value: str, base: Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    candidate = base / path
    if candidate.exists():
        return candidate
    return path.resolve()


def load_manifest_frames(analysis_dir: Path) -> list[dict[str, Any]]:
    manifest = read_json(analysis_dir / "frame_manifest.json")
    frames = manifest.get("frames", manifest if isinstance(manifest, list) else [])
    resolved = []
    project_base = Path.cwd()
    for item in frames:
        path_value = str(item["path"])
        frame_path = resolve_path(path_value, project_base)
        if not frame_path.exists():
            frame_path = resolve_path(path_value, analysis_dir)
        if not frame_path.exists():
            continue
        resolved.append(
            {
                "timestamp": float(item.get("timestamp_sec_approx", item.get("timestamp", 0.0))),
                "path": frame_path,
            }
        )
    return resolved


def visual_metrics(path: Path) -> tuple[float, float, float, float]:
    img = Image.open(path).convert("RGB").resize((160, 284), Image.Resampling.LANCZOS)
    arr = np.asarray(img).astype(np.float32)
    gray = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2])
    brightness = float(gray.mean())
    contrast = float(gray.std())
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))
    edge_density = float((gx.mean() + gy.mean()) / 2.0)
    white_fraction = float(np.mean((arr[:, :, 0] > 235) & (arr[:, :, 1] > 235) & (arr[:, :, 2] > 235)))
    return brightness, contrast, edge_density, white_fraction


def extract_video_frames(video_path: Path, frame_dir: Path, interval: float, max_frames: int, width: int) -> list[FrameSample]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    pattern = frame_dir / "frame_%04d.jpg"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(video_path),
            "-vf",
            f"fps=1/{interval:.4f},scale={width}:-2:flags=lanczos",
            "-frames:v",
            str(max_frames),
            "-q:v",
            "2",
            str(pattern),
        ]
    )
    samples: list[FrameSample] = []
    for idx, path in enumerate(sorted(frame_dir.glob("frame_*.jpg"))):
        timestamp = idx * interval
        brightness, contrast, edge_density, white_fraction = visual_metrics(path)
        samples.append(FrameSample(timestamp, path, brightness, contrast, edge_density, white_fraction))
    return samples


def extract_dense_window(video_path: Path, frame_dir: Path, start: float, end: float, fps: float, width: int) -> list[FrameSample]:
    frame_dir.mkdir(parents=True, exist_ok=True)
    duration = max(0.25, end - start)
    pattern = frame_dir / "dense_%04d.jpg"
    run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{duration:.3f}",
            "-i",
            str(video_path),
            "-vf",
            f"fps={fps:.4f},scale={width}:-2:flags=lanczos",
            "-q:v",
            "2",
            str(pattern),
        ]
    )
    interval = 1.0 / fps
    samples: list[FrameSample] = []
    for idx, path in enumerate(sorted(frame_dir.glob("dense_*.jpg"))):
        timestamp = start + idx * interval
        brightness, contrast, edge_density, white_fraction = visual_metrics(path)
        samples.append(FrameSample(timestamp, path, brightness, contrast, edge_density, white_fraction))
    return samples


def nearest_frame(frames: list[dict[str, Any]], timestamp: float) -> dict[str, Any] | None:
    if not frames:
        return None
    return min(frames, key=lambda item: abs(float(item["timestamp"]) - timestamp))


def nearest_sample(samples: list[FrameSample], timestamp: float) -> FrameSample | None:
    if not samples:
        return None
    return min(samples, key=lambda item: abs(item.timestamp - timestamp))


def frame_vector(path: Path) -> np.ndarray:
    img = Image.open(path).convert("L").resize((72, 128), Image.Resampling.BILINEAR)
    return np.asarray(img).astype(np.float32) / 255.0


def diff_score(path_a: Path | None, path_b: Path | None) -> float | None:
    if not path_a or not path_b or not path_a.exists() or not path_b.exists():
        return None
    return float(np.mean(np.abs(frame_vector(path_a) - frame_vector(path_b))))


def copy_labeled_cell(source: Path, label: str, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    img = Image.open(source).convert("RGB")
    scale = min(target_w / img.width, (target_h - 42) / img.height)
    resized = img.resize((int(img.width * scale), int(img.height * scale)), Image.Resampling.LANCZOS)
    cell = Image.new("RGB", size, "#111111")
    x = (target_w - resized.width) // 2
    y = 38 + max(0, (target_h - 42 - resized.height) // 2)
    cell.paste(resized, (x, y))
    draw = ImageDraw.Draw(cell)
    draw.rectangle((0, 0, target_w, 34), fill="#0B1220")
    draw.text((10, 8), label[:52], font=FONT_SMALL, fill="#FFFFFF")
    return cell


def make_side_by_side_sheet(
    reference_frames: list[dict[str, Any]],
    candidate_samples: list[FrameSample],
    output_path: Path,
    duration: float,
) -> list[dict[str, Any]]:
    rows = []
    seconds = list(range(0, int(math.ceil(duration))))
    cell_w, cell_h = 260, 510
    sheet = Image.new("RGB", (cell_w * 2, cell_h * len(seconds)), "#000000")
    for row_idx, sec in enumerate(seconds):
        ref = nearest_frame(reference_frames, sec)
        cand = nearest_sample(candidate_samples, sec)
        ref_path = Path(ref["path"]) if ref else None
        cand_path = cand.path if cand else None
        ref_prev = nearest_frame(reference_frames, max(0, sec - 1))
        cand_prev = nearest_sample(candidate_samples, max(0, sec - 1))
        ref_change = diff_score(Path(ref_prev["path"]) if ref_prev else None, ref_path)
        cand_change = diff_score(cand_prev.path if cand_prev else None, cand_path)
        rows.append(
            {
                "second": sec,
                "reference_frame": str(ref_path or ""),
                "candidate_frame": str(cand_path or ""),
                "reference_change": None if ref_change is None else round(ref_change, 4),
                "candidate_change": None if cand_change is None else round(cand_change, 4),
                "candidate_brightness": None if cand is None else round(cand.brightness, 2),
                "candidate_contrast": None if cand is None else round(cand.contrast, 2),
                "candidate_edge_density": None if cand is None else round(cand.edge_density, 3),
                "candidate_white_fraction": None if cand is None else round(cand.white_fraction, 4),
            }
        )
        if ref_path:
            sheet.paste(copy_labeled_cell(ref_path, f"REF {sec:02d}s", (cell_w, cell_h)), (0, row_idx * cell_h))
        if cand_path:
            sheet.paste(copy_labeled_cell(cand_path, f"FINAL {sec:02d}s", (cell_w, cell_h)), (cell_w, row_idx * cell_h))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=92)
    return rows


def make_dense_sheet(samples: list[FrameSample], output_path: Path, title: str) -> None:
    if not samples:
        return
    cell_w, cell_h = 220, 430
    cols = 5
    rows = math.ceil(len(samples) / cols)
    title_h = 52
    sheet = Image.new("RGB", (cell_w * cols, title_h + cell_h * rows), "#000000")
    draw = ImageDraw.Draw(sheet)
    draw.rectangle((0, 0, sheet.width, title_h), fill="#111827")
    draw.text((16, 14), title[:90], font=FONT_TITLE, fill="#FFFFFF")
    for idx, sample in enumerate(samples):
        x = (idx % cols) * cell_w
        y = title_h + (idx // cols) * cell_h
        label = f"{sample.timestamp:.2f}s W:{sample.white_fraction:.2f} E:{sample.edge_density:.2f}"
        sheet.paste(copy_labeled_cell(sample.path, label, (cell_w, cell_h)), (x, y))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, quality=92)


def risk_tags_for_segment(segment: dict[str, Any]) -> list[str]:
    haystack = f"{segment.get('text', '')} {segment.get('visual', '')}".lower()
    return sorted(tag for tag in RISK_KEYWORDS if tag in haystack)


def load_shot_plan(path: Path | None) -> tuple[list[dict[str, Any]], str]:
    if not path:
        return [], ""
    data = read_json(path)
    segments = data.get("segments") or []
    return segments, str(data.get("spoken_script", ""))


def write_timeline_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "second",
        "reference_change",
        "candidate_change",
        "candidate_brightness",
        "candidate_contrast",
        "candidate_edge_density",
        "candidate_white_fraction",
        "reference_frame",
        "candidate_frame",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_review_checklist(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Ad Quality Gate Review",
        "",
        f"Status: `{report['status']}`",
        f"Candidate: `{report['candidate_video']}`",
        "",
        "## Failures",
        "",
    ]
    if report["failures"]:
        lines.extend(f"- [ ] {item}" for item in report["failures"])
    else:
        lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    if report["warnings"]:
        lines.extend(f"- [ ] {item}" for item in report["warnings"])
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Required Visual Review",
            "",
            f"- [ ] Open `{report['side_by_side_sheet']}` and compare every second against the reference.",
            "- [ ] Confirm each visual beat supports the words being spoken at that moment.",
            "- [ ] Confirm captions do not hide faces, hands, phone screens, or product proof.",
            "- [ ] Confirm every product/phone/laptop screen shows real product pixels or an intentional designed overlay.",
            "- [ ] For phone shots, inspect the physical phone screen itself, not only a floating overlay card.",
            "",
            "## Dense Risky Windows",
            "",
        ]
    )
    for item in report["dense_risky_windows"]:
        lines.append(
            f"- [ ] Segment {item['segment_index']} ({item['start']}-{item['end']}s, "
            f"{', '.join(item['tags'])}): `{item['sheet']}`"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def evaluate(args: argparse.Namespace) -> dict[str, Any]:
    candidate_video = Path(args.candidate).expanduser().resolve()
    if not candidate_video.exists():
        raise FileNotFoundError(f"Candidate video not found: {candidate_video}")

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "quality_gate_report.json"
    candidate_duration = probe_duration(candidate_video)

    reference_frames: list[dict[str, Any]] = []
    reference_duration = None
    reference_transcript: dict[str, Any] = {}
    if args.reference_analysis_dir:
        reference_dir = Path(args.reference_analysis_dir).expanduser().resolve()
        reference_frames = load_manifest_frames(reference_dir)
        mechanism = read_json(reference_dir / "mechanism_brief.json") if (reference_dir / "mechanism_brief.json").exists() else {}
        reference_duration = mechanism.get("duration_sec")
        transcript_path = reference_dir / "transcript_summary.json"
        if transcript_path.exists():
            reference_transcript = read_json(transcript_path)

    candidate_transcript: dict[str, Any] = {}
    if args.candidate_transcript_summary:
        candidate_transcript = read_json(Path(args.candidate_transcript_summary).expanduser().resolve())

    shot_segments, planned_script = load_shot_plan(Path(args.shot_plan).expanduser().resolve() if args.shot_plan else None)

    max_frames = max(1, int(math.ceil(candidate_duration / args.sample_interval_sec)) + 2)
    candidate_samples = extract_video_frames(
        candidate_video,
        output_dir / "candidate_frames_1s",
        args.sample_interval_sec,
        max_frames,
        args.frame_width,
    )

    side_by_side_path = output_dir / "reference_vs_candidate_seconds.jpg"
    timeline_rows = make_side_by_side_sheet(
        reference_frames,
        candidate_samples,
        side_by_side_path,
        max(candidate_duration, float(reference_duration or 0.0)),
    )
    write_timeline_csv(output_dir / "timeline_seconds.csv", timeline_rows)

    dense_reports = []
    for idx, segment in enumerate(shot_segments, start=1):
        tags = risk_tags_for_segment(segment)
        if not tags:
            continue
        start = max(0.0, float(segment.get("start", 0.0)) - args.dense_pad_sec)
        end = min(candidate_duration, float(segment.get("end", start + 0.5)) + args.dense_pad_sec)
        dense_dir = output_dir / f"dense_{idx:02d}_{normalize_text('_'.join(tags))[:36]}"
        dense_samples = extract_dense_window(candidate_video, dense_dir, start, end, args.dense_fps, args.dense_width)
        dense_sheet = output_dir / f"dense_{idx:02d}_{normalize_text('_'.join(tags))[:36]}.jpg"
        make_dense_sheet(dense_samples, dense_sheet, f"{idx:02d} {start:.2f}-{end:.2f}s risk: {', '.join(tags)}")
        white_max = max((s.white_fraction for s in dense_samples), default=0.0)
        edge_min = min((s.edge_density for s in dense_samples), default=0.0)
        blank_screen_risk = bool(
            {"phone", "screen", "ui", "cta", "website"} & set(tags)
            and white_max >= args.white_fraction_warn
            and edge_min <= args.edge_density_warn
        )
        dense_reports.append(
            {
                "segment_index": idx,
                "start": round(start, 3),
                "end": round(end, 3),
                "tags": tags,
                "sheet": str(dense_sheet),
                "frame_count": len(dense_samples),
                "white_fraction_max": round(white_max, 4),
                "edge_density_min": round(edge_min, 4),
                "blank_screen_risk": blank_screen_risk,
                "review_required": True,
            }
        )

    failures: list[str] = []
    warnings: list[str] = []

    if reference_duration is not None:
        duration_delta = abs(candidate_duration - float(reference_duration))
        if duration_delta > args.duration_tolerance_sec:
            failures.append(
                f"Duration differs from reference by {duration_delta:.2f}s "
                f"(candidate {candidate_duration:.2f}s, reference {float(reference_duration):.2f}s)."
            )
    else:
        duration_delta = None

    if args.raw_voiceover and args.final_voiceover:
        raw_duration = probe_duration(Path(args.raw_voiceover).expanduser().resolve())
        final_duration = probe_duration(Path(args.final_voiceover).expanduser().resolve())
        voice_speed_factor = raw_duration / max(0.01, final_duration)
        if voice_speed_factor > args.max_voice_speed_factor:
            failures.append(
                f"Voice was speed-compressed {voice_speed_factor:.2f}x; rewrite or regenerate the read instead."
            )
        elif voice_speed_factor > args.warn_voice_speed_factor:
            warnings.append(f"Voice was speed-compressed {voice_speed_factor:.2f}x.")
    else:
        raw_duration = None
        final_duration = None
        voice_speed_factor = None

    if candidate_transcript:
        words = word_count_from_summary(candidate_transcript)
        span = speech_span(candidate_transcript, candidate_duration)
        words_per_second = words / max(0.01, span)
        if words_per_second > args.max_words_per_second:
            failures.append(f"Speech rate is {words_per_second:.2f} words/sec; likely sounds rushed or synthetic.")
    else:
        words = None
        span = None
        words_per_second = None
        warnings.append("No candidate transcript summary provided; audio/context checks were limited.")

    planned_norm = normalize_text(planned_script)
    actual_norm = normalize_text(transcript_text(candidate_transcript)) if candidate_transcript else ""
    for term in args.required_spoken_term or []:
        term_norm = normalize_text(term)
        if not term_norm:
            continue
        term_forms = {
            term_norm,
            term_norm.replace(" dot ", " "),
            term_norm.replace(" ", ""),
        }
        actual_forms = {actual_norm, actual_norm.replace(" dot ", " "), actual_norm.replace(" ", "")}
        planned_forms = {planned_norm, planned_norm.replace(" dot ", " "), planned_norm.replace(" ", "")}
        in_actual = any(form and any(form in actual for actual in actual_forms) for form in term_forms)
        in_plan = any(form and any(form in planned for planned in planned_forms) for form in term_forms)
        if not in_actual:
            warnings.append(f"Required spoken term may not have transcribed correctly: {term!r}.")
        if not in_plan:
            warnings.append(f"Required spoken term is not present in the shot plan script: {term!r}.")

    for item in dense_reports:
        if item["blank_screen_risk"]:
            failures.append(
                f"Dense risky window {item['segment_index']} has high-white/low-detail frames; inspect {item['sheet']}."
            )
    if dense_reports:
        warnings.append(
            f"{len(dense_reports)} dense risky windows require visual inspection before delivery."
        )

    low_change_pairs = []
    for row in timeline_rows:
        ref_change = row.get("reference_change")
        cand_change = row.get("candidate_change")
        if isinstance(ref_change, float) and isinstance(cand_change, float):
            if ref_change > args.reference_cut_threshold and cand_change < args.candidate_static_threshold:
                low_change_pairs.append(row["second"])
    if low_change_pairs:
        warnings.append(
            "Reference changes while candidate is relatively static around seconds: "
            + ", ".join(str(s) for s in low_change_pairs[:12])
        )

    status = "failed" if failures else "passed_with_warnings" if warnings else "passed"
    checklist_path = output_dir / "manual_review_checklist.md"
    report = {
        "status": status,
        "created_at_utc": utc_now(),
        "candidate_video": str(candidate_video),
        "output_dir": str(output_dir),
        "reference_analysis_dir": str(Path(args.reference_analysis_dir).expanduser().resolve()) if args.reference_analysis_dir else "",
        "candidate_duration_sec": round(candidate_duration, 3),
        "reference_duration_sec": reference_duration,
        "duration_delta_sec": None if duration_delta is None else round(duration_delta, 3),
        "candidate_words": words,
        "candidate_speech_span_sec": None if span is None else round(span, 3),
        "candidate_words_per_second": None if words_per_second is None else round(words_per_second, 3),
        "raw_voiceover_duration_sec": None if raw_duration is None else round(raw_duration, 3),
        "final_voiceover_duration_sec": None if final_duration is None else round(final_duration, 3),
        "voice_speed_factor": None if voice_speed_factor is None else round(voice_speed_factor, 4),
        "side_by_side_sheet": str(side_by_side_path),
        "timeline_csv": str(output_dir / "timeline_seconds.csv"),
        "manual_review_checklist": str(checklist_path),
        "dense_risky_windows": dense_reports,
        "reference_hook": reference_transcript.get("hook_window_0_5s", ""),
        "candidate_hook": candidate_transcript.get("hook_window_0_5s", ""),
        "reference_cta": reference_transcript.get("cta_window_last_7s", ""),
        "candidate_cta": candidate_transcript.get("cta_window_last_7s", ""),
        "failures": failures,
        "warnings": warnings,
        "review_rule": (
            "Any dense risky window marked review_required must be visually inspected. "
            "Failures block delivery; warnings require an explicit decision."
        ),
    }
    write_json(report_path, report)
    write_review_checklist(checklist_path, report)
    print("RESULT: " + json.dumps({"status": status, "report": str(report_path), "failures": failures, "warnings": warnings}))
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a reference-driven ad quality gate.")
    parser.add_argument("--candidate", required=True, help="Final candidate MP4.")
    parser.add_argument("--output-dir", required=True, help="Directory for QC artifacts.")
    parser.add_argument("--reference-analysis-dir", default="", help="Output dir from understand_ad_video.py for the reference.")
    parser.add_argument("--candidate-transcript-summary", default="", help="Groq transcript summary JSON for candidate.")
    parser.add_argument("--shot-plan", default="", help="Script/shot-plan JSON with segments.")
    parser.add_argument("--raw-voiceover", default="", help="Raw pre-speed-fit voiceover audio.")
    parser.add_argument("--final-voiceover", default="", help="Final voiceover audio used in the master.")
    parser.add_argument("--required-spoken-term", action="append", help="Term that must survive transcription.")
    parser.add_argument("--sample-interval-sec", type=float, default=1.0)
    parser.add_argument("--frame-width", type=int, default=360)
    parser.add_argument("--dense-fps", type=float, default=4.0)
    parser.add_argument("--dense-pad-sec", type=float, default=0.35)
    parser.add_argument("--dense-width", type=int, default=360)
    parser.add_argument("--duration-tolerance-sec", type=float, default=0.5)
    parser.add_argument("--warn-voice-speed-factor", type=float, default=1.06)
    parser.add_argument("--max-voice-speed-factor", type=float, default=1.12)
    parser.add_argument("--max-words-per-second", type=float, default=3.65)
    parser.add_argument("--white-fraction-warn", type=float, default=0.3)
    parser.add_argument("--edge-density-warn", type=float, default=2.6)
    parser.add_argument("--reference-cut-threshold", type=float, default=0.13)
    parser.add_argument("--candidate-static-threshold", type=float, default=0.045)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_binary("ffmpeg")
    require_binary("ffprobe")
    report = evaluate(args)
    return 1 if report["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run ugc-ai-ad recipe test iterations (intake -> character -> clips -> assemble -> QC).

Hardcoded params at top — run from repo root:
    python3 .agents/skills/super-video-maker/tools/ugc_ad_runner.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# --- Hardcoded test config (edit and press play) ---
JOB_ID = "ugc_ad_test_20260521"
PRODUCT_NAME = "Acme"
OFFER = "SEO articles + backlinks on autopilot"
ICP = "SaaS founders drowning in content calendars"
PAIN = "publishing 4 blog posts a month manually"
CTA = "Start free at example.com"
VISUAL_SEED = 18427
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
MAX_ITERATIONS = 3
START_ITERATION = 1
REUSE_HERO_FROM_ITERATION = 1
CLIP_DURATION = "5"
CLIP_RESOLUTION = "720p"
USE_FAST_SEEDANCE = True
GENERATE_AUDIO = False
# ---

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path.cwd().resolve()
if not (REPO_ROOT / ".env").exists():
    for parent in Path(__file__).resolve().parents:
        if (parent / ".env").exists():
            REPO_ROOT = parent
            break

JOB_DIR = REPO_ROOT / "tmp" / "video_jobs" / JOB_ID
IMAGE_TOOL = SKILL_DIR / "tools" / "image_provider.py"
SEEDANCE_TOOL = SKILL_DIR / "tools" / "fal_seedance_video.py"
REPLICATE_TOOL = SKILL_DIR / "tools" / "replicate_video.py"
QC_TOOL = SKILL_DIR / "tools" / "ffmpeg_qc.py"
ORCH_TOOL = SKILL_DIR / "tools" / "video_orchestrator.py"

CREATOR_PROMPT = (
    "Vertical phone portrait of a distinct fictional UGC creator, woman in her early 30s, "
    "natural imperfect skin, casual beige sweater, real home office background, window light, "
    "candid talking-to-camera energy, no beauty filter, no logos, no text, no subtitles, "
    "photorealistic phone camera, shallow depth of field."
)
CREATOR_MEDIUM_PROMPT = (
    "Same fictional UGC creator from reference, medium shot waist-up, holding phone at chest "
    "height, natural home office, same wardrobe family, realistic skin texture, no logos, "
    "no text, no subtitles, phone-camera realism."
)

HOOKS = [
    {
        "id": "confession",
        "family": "confession",
        "first_frame": "I almost quit SEO",
        "line": "I almost quit SEO because writing took my entire Sunday.",
    },
    {
        "id": "problem",
        "family": "problem-callout",
        "first_frame": "4 posts/month?",
        "line": "If you are still publishing four posts a month manually, watch this.",
    },
    {
        "id": "demo",
        "family": "demo-first",
        "first_frame": "Watch the calendar",
        "line": "Watch what happens when I queue a month of SEO articles in one sitting.",
    },
]

KEN_BURNS_PROMPTS = {
    "demo": (
        "Over-shoulder view of a laptop showing a generic SEO content calendar dashboard, "
        "no brand logos, natural home office, documentary photo, 9:16 vertical framing."
    ),
    "cta": (
        "Close portrait of the same fictional UGC creator smiling casually at camera, "
        "home office background, natural window light, phone-camera realism, vertical 9:16."
    ),
}

BEAT_PROMPTS = {
    "hook": (
        "@Image1 shows the fictional UGC creator. Handheld vertical phone video, same face, "
        "same hair, same wardrobe, speaking urgently to camera with slight handheld motion, "
        "natural room tone, believable exposure, no subtitles in footage, no logos, no face morphing."
    ),
    "demo": (
        "@Image1 and @Image2 show the same fictional creator. Over-shoulder phone shot of a laptop "
        "with a generic SEO dashboard UI (no real brand logos), creator points at the screen, "
        "casual home office, natural light, handheld micro-movement, no subtitles in footage."
    ),
    "cta": (
        "@Image1 shows the same fictional creator. Close talking-head shot, relaxed smile, "
        "small nod, casual CTA energy, home office background, no subtitles in footage, no logos."
    ),
}


def emit(payload: dict) -> None:
    print("RESULT: " + json.dumps(payload), flush=True)


def log(msg: str) -> None:
    print(f"[ugc_ad_runner] {msg}", flush=True)


def parse_result(stdout: str) -> dict:
    for line in stdout.splitlines():
        if line.startswith("RESULT: "):
            return json.loads(line.replace("RESULT: ", "", 1))
    raise RuntimeError(f"No RESULT line in output:\n{stdout[-2000:]}")


def run_cmd(cmd: list[str], cwd: Path | None = None) -> dict:
    log("RUN " + " ".join(cmd[:6]) + (" ..." if len(cmd) > 6 else ""))
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if proc.stdout:
        print(proc.stdout, end="" if proc.stdout.endswith("\n") else "\n")
    if proc.stderr:
        print(proc.stderr, end="" if proc.stderr.endswith("\n") else "", file=sys.stderr)
    payload = None
    for stream in (proc.stdout, proc.stderr):
        if not stream:
            continue
        try:
            payload = parse_result(stream)
            break
        except RuntimeError:
            payload = None
    if payload is None:
        raise RuntimeError(proc.stderr or proc.stdout or f"exit {proc.returncode}")
    if payload.get("status") != "succeeded":
        raise RuntimeError(payload.get("error") or json.dumps(payload))
    if proc.returncode != 0:
        log(f"non-zero exit {proc.returncode} but RESULT succeeded")
    return payload


def copy_asset(src: str, dest: Path) -> Path:
    path = Path(src).expanduser()
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    log(f"copied {path.name} -> {dest}")
    return dest


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def stage_intake(iter_dir: Path) -> dict:
    brief = {
        "product": PRODUCT_NAME,
        "offer": OFFER,
        "icp": ICP,
        "pain": PAIN,
        "cta": CTA,
        "platform": "tiktok",
        "aspect_ratio": "9:16",
        "allowed_claims": ["automates SEO content workflow", "saves publishing time"],
        "banned_claims": ["guaranteed rankings", "instant traffic"],
    }
    write_json(iter_dir / "ad_brief.json", brief)
    write_json(
        iter_dir / "variant_matrix.json",
        {
            "hooks": HOOKS,
            "selected_for_batch": [h["id"] for h in HOOKS],
            "visual_seed": VISUAL_SEED,
            "voice_id": VOICE_ID,
        },
    )
    run_cmd(
        [
            sys.executable,
            str(ORCH_TOOL),
            "create",
            "--job-id",
            f"{JOB_ID}_iter{iter_dir.name.split('_')[-1]}",
            "--goal",
            f"UGC ad test {PRODUCT_NAME} {iter_dir.name}",
            "--platforms",
            "tiktok,instagram",
        ]
    )
    return brief


def stage_character(iter_dir: Path, iteration: int) -> dict:
    char_dir = iter_dir / "assets" / "character"
    char_dir.mkdir(parents=True, exist_ok=True)

    hero = char_dir / "creator_hero.png"
    reuse_hero = JOB_DIR / f"iteration_{REUSE_HERO_FROM_ITERATION}" / "assets" / "character" / "creator_hero.png"
    if reuse_hero.exists() and iteration > REUSE_HERO_FROM_ITERATION:
        copy_asset(str(reuse_hero), hero)
        log(f"reused hero from iteration_{REUSE_HERO_FROM_ITERATION}")
    elif not hero.exists():
        res = run_cmd(
            [
                sys.executable,
                str(IMAGE_TOOL),
                "generate",
                "--prompt",
                CREATOR_PROMPT,
                "--size",
                "1024x1536",
                "--quality",
                "high",
                "--output-format",
                "jpeg",
            ]
        )
        copy_asset(res["local_path"], hero)

    medium = char_dir / "creator_medium_phone.png"
    if iteration >= 2 and not medium.exists():
        res = run_cmd(
            [
                sys.executable,
                str(IMAGE_TOOL),
                "edit",
                "--reference-image",
                str(hero),
                "--prompt",
                CREATOR_MEDIUM_PROMPT,
                "--size",
                "1024x1536",
                "--quality",
                "high",
                "--output-format",
                "jpeg",
            ]
        )
        copy_asset(res["local_path"], medium)

    refs = [str(hero)]
    if medium.exists():
        refs.append(str(medium))

    card = {
        "creator_name": "Jordan Ellis",
        "bio": "Fictional SaaS marketer, not a real person",
        "visual_seed": VISUAL_SEED,
        "voice_id": VOICE_ID,
        "reference_images": refs,
        "negative_prompts": [
            "subtitles in footage",
            "logos",
            "beauty filter",
            "studio lighting",
        ],
    }
    write_json(char_dir / "character_card.json", card)
    return card


def ken_burns_from_still(still_path: Path, out_path: Path, seconds: int = 5) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        str(still_path),
        "-vf",
        (
            "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
            f"zoompan=z='min(zoom+0.0012,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={seconds * 30}:s=1080x1920:fps=30"
        ),
        "-t",
        str(seconds),
        "-pix_fmt",
        "yuv420p",
        "-an",
        str(out_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)


def generate_still_for_beat(beat: str, card: dict) -> Path:
    hero = Path(card["reference_images"][0])
    prompt = KEN_BURNS_PROMPTS.get(beat)
    if not prompt:
        raise ValueError(f"No ken burns prompt for beat {beat}")
    if beat == "cta" and len(card["reference_images"]) > 1:
        res = run_cmd(
            [
                sys.executable,
                str(IMAGE_TOOL),
                "edit",
                "--reference-image",
                str(hero),
                "--prompt",
                prompt,
                "--size",
                "1024x1536",
                "--quality",
                "high",
                "--output-format",
                "jpeg",
            ]
        )
    else:
        res = run_cmd(
            [
                sys.executable,
                str(IMAGE_TOOL),
                "generate",
                "--prompt",
                prompt,
                "--size",
                "1024x1536",
                "--quality",
                "high",
                "--output-format",
                "jpeg",
            ]
        )
    still_dir = hero.parent.parent / "stills"
    still_dir.mkdir(parents=True, exist_ok=True)
    dest = still_dir / f"{beat}_kenburns.jpg"
    copy_asset(res["local_path"], dest)
    return dest


def generate_clip_with_providers(prompt: str, refs: list[str]) -> dict:
    fal_cmd = [
        sys.executable,
        str(SEEDANCE_TOOL),
        "generate",
        "--mode",
        "reference",
        "--prompt",
        prompt,
        "--duration",
        CLIP_DURATION,
        "--resolution",
        CLIP_RESOLUTION,
        "--aspect-ratio",
        "9:16",
        "--seed",
        str(VISUAL_SEED),
    ]
    if USE_FAST_SEEDANCE:
        fal_cmd.append("--fast")
    if GENERATE_AUDIO:
        fal_cmd.append("--generate-audio")
    else:
        fal_cmd.append("--no-generate-audio")
    for ref in refs[:2]:
        fal_cmd.extend(["--reference-image", ref])

    try:
        return run_cmd(fal_cmd)
    except Exception as fal_exc:
        log(f"fal failed, trying replicate: {fal_exc}")
        rep_cmd = [
            sys.executable,
            str(REPLICATE_TOOL),
            "generate",
            "--prompt",
            prompt,
            "--duration",
            int(CLIP_DURATION),
            "--resolution",
            CLIP_RESOLUTION,
            "--aspect-ratio",
            "9:16",
            "--seed",
            str(VISUAL_SEED),
        ]
        if GENERATE_AUDIO:
            rep_cmd.append("--generate-audio")
        for ref in refs[:2]:
            rep_cmd.extend(["--reference-image", ref])
        return run_cmd(rep_cmd)


def stage_clip(
    iter_dir: Path,
    beat: str,
    hook: dict | None,
    card: dict,
    clip_index: int,
) -> dict:
    clips_dir = iter_dir / "assets" / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)

    name = f"{beat}_{hook['id'] if hook else 'shared'}_{clip_index}.mp4"
    dest = clips_dir / name
    if dest.exists() and dest.stat().st_size > 50_000:
        log(f"skip existing clip {name}")
        return {
            "beat": beat,
            "hook_id": hook["id"] if hook else None,
            "path": str(dest.relative_to(REPO_ROOT)),
            "seed": VISUAL_SEED,
            "skipped": True,
        }

    prompt = BEAT_PROMPTS[beat]
    if beat == "hook" and hook:
        prompt = (
            f"{prompt} She says with casual frustration: '{hook['line']}'"
        )

    refs = card["reference_images"]
    provider = "fal"
    try:
        res = generate_clip_with_providers(prompt, refs)
        copy_asset(res["local_path"], dest)
    except Exception as video_exc:
        log(f"video providers failed for {beat}: {video_exc}")
        if beat == "hook":
            prior_hooks = sorted((JOB_DIR / "iteration_1" / "assets" / "clips").glob("hook_*.mp4"))
            if prior_hooks:
                copy_asset(str(prior_hooks[0]), dest)
                provider = "reuse_prior_hook"
                res = {"seed": VISUAL_SEED, "elapsed_s": 0}
            else:
                still = Path(refs[0])
                ken_burns_from_still(still, dest, seconds=int(CLIP_DURATION))
                provider = "ken_burns_from_hero"
                res = {"seed": VISUAL_SEED, "elapsed_s": 0}
        elif beat in KEN_BURNS_PROMPTS:
            provider = "ken_burns"
            still = generate_still_for_beat(beat, card)
            ken_burns_from_still(still, dest, seconds=int(CLIP_DURATION))
            res = {"seed": VISUAL_SEED, "elapsed_s": 0}
        else:
            raise

    meta = {
        "beat": beat,
        "hook_id": hook["id"] if hook else None,
        "path": str(dest.relative_to(REPO_ROOT)),
        "seed": res.get("seed", VISUAL_SEED),
        "elapsed_s": res.get("elapsed_s"),
        "provider": provider,
    }
    return meta


def assemble_variant(iter_dir: Path, clip_paths: list[Path], out_name: str) -> Path:
    final_dir = iter_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    out_path = final_dir / out_name

    concat_list = iter_dir / "build" / "concat.txt"
    concat_list.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"file '{p.resolve()}'" for p in clip_paths]
    concat_list.write_text("\n".join(lines) + "\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-vf",
        "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11",
        str(out_path),
    ]
    log("assemble " + out_name)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return out_path


def stage_qc(video_path: Path) -> dict:
    try:
        return run_cmd([sys.executable, str(QC_TOOL), str(video_path)])
    except Exception as exc:
        return {"status": "failed", "error": str(exc), "path": str(video_path)}


def run_iteration(iteration: int) -> dict:
    iter_dir = JOB_DIR / f"iteration_{iteration}"
    iter_dir.mkdir(parents=True, exist_ok=True)
    log(f"=== ITERATION {iteration} / {MAX_ITERATIONS} ===")

    notes: list[str] = []
    clip_metas: list[dict] = []

    stage_intake(iter_dir)
    card = stage_character(iter_dir, iteration)

    if iteration == 1:
        clip_metas.append(stage_clip(iter_dir, "hook", HOOKS[0], card, 1))
        clip_metas.append(stage_clip(iter_dir, "cta", None, card, 2))
        clips = [
            iter_dir / "assets" / "clips" / f"hook_{HOOKS[0]['id']}_1.mp4",
            iter_dir / "assets" / "clips" / f"cta_shared_2.mp4",
        ]
        final = assemble_variant(iter_dir, clips, "vertical_9x16_v1.mp4")
        notes.append("v1: smoke test hook+cta only, single reference image")

    elif iteration == 2:
        clip_metas.append(stage_clip(iter_dir, "hook", HOOKS[1], card, 1))
        clip_metas.append(stage_clip(iter_dir, "demo", None, card, 2))
        clip_metas.append(stage_clip(iter_dir, "cta", None, card, 3))
        clips = [
            iter_dir / "assets" / "clips" / f"hook_{HOOKS[1]['id']}_1.mp4",
            iter_dir / "assets" / "clips" / "demo_shared_2.mp4",
            iter_dir / "assets" / "clips" / "cta_shared_3.mp4",
        ]
        final = assemble_variant(iter_dir, clips, "vertical_9x16_v2.mp4")
        notes.append("v2: added creator_medium ref + demo beat in middle")

    else:
        finals = []
        demo_meta = stage_clip(iter_dir, "demo", None, card, 2)
        cta_meta = stage_clip(iter_dir, "cta", None, card, 3)
        clip_metas.extend([demo_meta, cta_meta])
        demo_path = iter_dir / "assets" / "clips" / "demo_shared_2.mp4"
        cta_path = iter_dir / "assets" / "clips" / "cta_shared_3.mp4"

        for idx, hook in enumerate(HOOKS, start=1):
            hook_meta = stage_clip(iter_dir, "hook", hook, card, idx * 10 + 1)
            clip_metas.append(hook_meta)
            hook_path = iter_dir / "assets" / "clips" / f"hook_{hook['id']}_{idx * 10 + 1}.mp4"
            out = assemble_variant(
                iter_dir,
                [hook_path, demo_path, cta_path],
                f"vertical_9x16_{hook['id']}.mp4",
            )
            finals.append(str(out.relative_to(REPO_ROOT)))
            write_json(iter_dir / "qc" / f"{hook['id']}_qc.json", stage_qc(out))

        notes.append("v3: three hook variants sharing one demo+cta body")
        final = Path(finals[0])

    qc = stage_qc(final)
    write_json(iter_dir / "qc" / "master_qc.json", qc)

    if iteration < 3:
        duration = qc.get("metrics", {}).get("duration_seconds") or qc.get("duration")
        if not duration or (isinstance(duration, (int, float)) and duration < 8):
            notes.append("QC WARN: master shorter than 8s — check clip concat")
        if qc.get("status") != "succeeded":
            notes.append(f"QC FAIL: {qc.get('error', 'unknown')}")

    write_json(
        iter_dir / "qc_notes.txt",
        {"iteration": iteration, "notes": notes, "clips": clip_metas, "qc": qc},
    )

    return {
        "iteration": iteration,
        "final": str(final.relative_to(REPO_ROOT)) if final.exists() else None,
        "finals": finals if iteration == 3 else None,
        "qc_status": qc.get("status"),
        "notes": notes,
    }


def main() -> None:
    global START_ITERATION
    load_dotenv(REPO_ROOT / ".env")
    JOB_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        try:
            START_ITERATION = int(sys.argv[1])
        except ValueError:
            pass

    if not os.getenv("OPENAI_API_KEY"):
        emit({"status": "failed", "error": "OPENAI_API_KEY missing"})
        sys.exit(2)
    if not (os.getenv("FALAI_API_KEY") or os.getenv("FAL_KEY")):
        emit({"status": "failed", "error": "FALAI_API_KEY missing"})
        sys.exit(2)

    prior = []
    summary_path = JOB_DIR / "iteration_summary.json"
    if summary_path.exists():
        prior = json.loads(summary_path.read_text()).get("results", [])

    results = [r for r in prior if r.get("iteration", 0) < START_ITERATION]
    for i in range(START_ITERATION, MAX_ITERATIONS + 1):
        try:
            results.append(run_iteration(i))
        except Exception as exc:
            log(f"ITERATION {i} FAILED: {exc}")
            results.append({"iteration": i, "status": "failed", "error": str(exc)})
            break

    write_json(JOB_DIR / "iteration_summary.json", {"results": results})
    emit(
        {
            "status": "succeeded" if all(r.get("qc_status") == "succeeded" for r in results if "qc_status" in r) else "partial",
            "stage": "ugc_ad_test",
            "job_id": JOB_ID,
            "job_dir": str(JOB_DIR.relative_to(REPO_ROOT)),
            "iterations": results,
        }
    )


if __name__ == "__main__":
    main()

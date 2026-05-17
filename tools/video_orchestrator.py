#!/usr/bin/env python3
"""Small job-state orchestrator for Super Video Maker.

This does not replace creative judgment. It gives agents a stable place to
create video jobs, save stage results, and resume work.
"""

import argparse
import json
import time
from pathlib import Path


def emit(payload):
    print("RESULT: " + json.dumps(payload), flush=True)


def jobs_root():
    root = Path.cwd() / "tmp" / "video_jobs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def state_path(job_id):
    return jobs_root() / job_id / "job_state.json"


def create_job(args):
    job_id = args.job_id or f"video_{time.strftime('%Y%m%d_%H%M%S')}"
    job_dir = jobs_root() / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    state = {
        "job_id": job_id,
        "status": "created",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "goal": args.goal,
        "platforms": args.platforms,
        "stages": [],
        "artifacts": [],
    }
    state_path(job_id).write_text(json.dumps(state, indent=2))
    emit({"status": "succeeded", "stage": "create_job", "job_id": job_id, "job_dir": str(job_dir)})


def add_stage(args):
    path = state_path(args.job_id)
    if not path.exists():
        emit({"status": "failed", "error": f"Unknown job_id: {args.job_id}"})
        return
    state = json.loads(path.read_text())
    state["stages"].append({
        "name": args.stage,
        "status": args.status,
        "note": args.note,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    path.write_text(json.dumps(state, indent=2))
    emit({"status": "succeeded", "stage": "add_stage", "job_id": args.job_id, "state_path": str(path)})


def show_job(args):
    path = state_path(args.job_id)
    if not path.exists():
        emit({"status": "failed", "error": f"Unknown job_id: {args.job_id}"})
        return
    emit({"status": "succeeded", "stage": "show_job", "job_state": json.loads(path.read_text())})


def build_parser():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--goal", required=True)
    create.add_argument("--platforms", default="youtube,tiktok,instagram")
    create.add_argument("--job-id")
    create.set_defaults(func=create_job)

    stage = sub.add_parser("stage")
    stage.add_argument("--job-id", required=True)
    stage.add_argument("--stage", required=True)
    stage.add_argument("--status", default="completed")
    stage.add_argument("--note", default="")
    stage.set_defaults(func=add_stage)

    show = sub.add_parser("show")
    show.add_argument("--job-id", required=True)
    show.set_defaults(func=show_job)
    return parser


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

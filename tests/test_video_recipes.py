#!/usr/bin/env python3
"""Pytest-free recipe tests (run directly or via video_recipes.py test)."""

import json
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
TOOL = SKILL_ROOT / "tools" / "video_recipes.py"


def run_cli(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        text=True,
        cwd=str(SKILL_ROOT),
    )
    lines = [line for line in proc.stdout.splitlines() if line.startswith("RESULT: ")]
    assert lines, f"No RESULT line. stderr={proc.stderr!r} stdout={proc.stdout!r}"
    payload = json.loads(lines[-1].replace("RESULT: ", "", 1))
    assert proc.returncode == 0, payload
    return payload


def test_list_has_nine_recipes():
    payload = run_cli("list")
    assert payload["recipe_count"] == 9


def test_validate_passes():
    payload = run_cli("validate")
    assert payload["status"] == "succeeded"


def test_match_tiktok_ad():
    payload = run_cli("match", "--goal", "TikTok ad for my SaaS waitlist")
    assert payload["best_match"]["recipe_id"] == "ugc-ai-ad"


def test_show_avatar_explainer():
    payload = run_cli("show", "avatar-explainer")
    assert payload["recipe"]["id"] == "avatar-explainer"
    assert len(payload["recipe"]["stages"]) >= 5


def test_registry_test_command():
    payload = run_cli("test")
    assert payload["status"] == "succeeded"
    assert payload["tests_failed"] == 0


if __name__ == "__main__":
    test_list_has_nine_recipes()
    test_validate_passes()
    test_match_tiktok_ad()
    test_show_avatar_explainer()
    test_registry_test_command()
    print("All recipe tests passed.")

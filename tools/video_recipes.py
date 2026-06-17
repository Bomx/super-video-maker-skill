#!/usr/bin/env python3
"""List, validate, match, and dry-run Super Video Maker recipes.

Recipes live in ../recipes/*.json relative to this skill folder.

Usage:
    python3 video_recipes.py list
    python3 video_recipes.py show avatar-explainer
    python3 video_recipes.py validate
    python3 video_recipes.py match --goal "TikTok ad for my SaaS waitlist"
    python3 video_recipes.py plan --recipe ugc-ai-ad --goal "Waitlist ad"
    python3 video_recipes.py test
"""

from __future__ import annotations

import argparse
import re
import json
import re
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
RECIPES_DIR = SKILL_ROOT / "recipes"
SCHEMA_PATH = RECIPES_DIR / "schema.json"
REQUIRED_TOP_LEVEL = {
    "id",
    "name",
    "version",
    "description",
    "best_for",
    "platforms",
    "aspect_ratios",
    "duration_seconds",
    "stages",
    "tools",
    "providers",
    "routing_keywords",
    "deliverables",
}
REQUIRED_STAGE = {"id", "title", "actions"}
VALID_ASPECTS = {"16:9", "9:16", "1:1", "4:5"}
VALID_VISUAL_JOBS = {"proof", "mechanism", "consequence", "action", "transition"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")


def emit(payload: dict) -> None:
    print("RESULT: " + json.dumps(payload), flush=True)


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def recipe_paths() -> list[Path]:
    return sorted(
        p for p in RECIPES_DIR.glob("*.json")
        if p.name != "schema.json"
    )


def load_recipe(path: Path) -> dict:
    return json.loads(path.read_text())


def load_all_recipes() -> dict[str, dict]:
    recipes = {}
    for path in recipe_paths():
        data = load_recipe(path)
        recipes[data["id"]] = data
    return recipes


def validate_duration_block(recipe_id: str, block: dict, errors: list[str]) -> None:
    for key in ("min", "max", "target"):
        if key not in block:
            errors.append(f"{recipe_id}: duration_seconds missing '{key}'")
            return
    if not (block["min"] <= block["target"] <= block["max"]):
        errors.append(
            f"{recipe_id}: duration_seconds must satisfy min <= target <= max"
        )


def validate_recipe(data: dict, recipes_by_id: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    recipe_id = data.get("id", "<unknown>")

    for field in REQUIRED_TOP_LEVEL:
        if field not in data:
            errors.append(f"{recipe_id}: missing required field '{field}'")

    if "id" in data:
        if not ID_PATTERN.match(data["id"]):
            errors.append(f"{recipe_id}: invalid id format")
        if data["id"] != recipe_id:
            errors.append(f"{recipe_id}: id field mismatch with expected slug")

    if "version" in data and not VERSION_PATTERN.match(str(data["version"])):
        errors.append(f"{recipe_id}: version must look like 1.0.0")

    if "aspect_ratios" in data:
        for ratio in data["aspect_ratios"]:
            if ratio not in VALID_ASPECTS:
                errors.append(f"{recipe_id}: invalid aspect ratio '{ratio}'")

    if "duration_seconds" in data:
        validate_duration_block(recipe_id, data["duration_seconds"], errors)

    stages = data.get("stages", [])
    if len(stages) < 3:
        errors.append(f"{recipe_id}: need at least 3 stages")

    stage_ids = []
    for stage in stages:
        missing = REQUIRED_STAGE - set(stage.keys())
        if missing:
            errors.append(f"{recipe_id}: stage missing {sorted(missing)}")
        else:
            stage_ids.append(stage["id"])
        if not stage.get("actions"):
            errors.append(f"{recipe_id}: stage '{stage.get('id')}' has no actions")

    if len(stage_ids) != len(set(stage_ids)):
        errors.append(f"{recipe_id}: duplicate stage ids")

    if "visual_jobs" in data:
        for job in data["visual_jobs"]:
            if job not in VALID_VISUAL_JOBS:
                errors.append(f"{recipe_id}: invalid visual job '{job}'")

    for tool_path in data.get("tools", []):
        rel = SKILL_ROOT / tool_path
        if not rel.exists():
            errors.append(f"{recipe_id}: missing tool file '{tool_path}'")

    if recipe_id in recipes_by_id and recipes_by_id[recipe_id] is not data:
        pass

    return errors


def validate_registry() -> dict:
    recipes = load_all_recipes()
    errors: list[str] = []
    ids = list(recipes.keys())

    if len(ids) < 2:
        errors.append("registry: expected at least 2 recipes")

    for recipe_id, data in recipes.items():
        errors.extend(validate_recipe(data, recipes))

    if len(ids) != len(set(ids)):
        errors.append("registry: duplicate recipe ids detected")

    return {
        "recipe_count": len(ids),
        "recipe_ids": sorted(ids),
        "errors": errors,
        "valid": not errors,
    }


def score_recipe(recipe: dict, goal: str) -> tuple[int, list[str]]:
    text = goal.lower()
    score = 0
    reasons: list[str] = []

    def has(token: str) -> bool:
        """word-boundary match — 'ad' must NOT fire on 'head'/'upload'"""
        return re.search(r"\b" + re.escape(token.lower()) + r"\b", text) is not None

    for keyword in recipe.get("routing_keywords", []):
        if has(keyword):
            score += 3
            reasons.append(f"+ keyword '{keyword}'")

    for keyword in recipe.get("routing_negative_keywords", []):
        if has(keyword):
            score -= 5
            reasons.append(f"- negative '{keyword}'")

    for phrase in recipe.get("best_for", []):
        words = phrase.lower().split()
        if words and all(has(w) for w in words[:2]):
            score += 2
            reasons.append(f"+ best_for overlap '{phrase}'")

    if has("ad") or has("ads") or has("tiktok") or has("reels"):
        if recipe["id"] == "ugc-ai-ad":
            score += 4
            reasons.append("+ platform ad signal -> ugc-ai-ad")
        if recipe["id"] == "faceless-broll-ad" and has("faceless"):
            score += 4
            reasons.append("+ faceless ad signal")

    if any(has(t) for t in ("news", "explainer", "trending", "update")):
        if recipe["id"] == "avatar-explainer":
            score += 4
            reasons.append("+ news/explainer signal -> avatar-explainer")

    if any(has(t) for t in ("demo", "walkthrough", "screencast", "saas")):
        if recipe["id"] in {"screencast-demo", "avatar-product-walkthrough"}:
            score += 3
            reasons.append("+ demo signal")

    if any(has(t) for t in ("repurpose", "podcast", "webinar", "shorts from")):
        if recipe["id"] == "longform-repurpose":
            score += 5
            reasons.append("+ repurpose signal")

    if any(has(t) for t in ("remotion", "motion graphics", "kinetic")):
        if recipe["id"] == "motion-graphics":
            score += 5
            reasons.append("+ motion graphics signal")

    if any(token in text for token in ("proof", "browser", "verify", "source receipt")):
        if recipe["id"] == "agent-browser-proof":
            score += 5
            reasons.append("+ proof clip signal")

    if "caption" in text and "existing" in text:
        if recipe["id"] == "captioned-talking-head":
            score += 5
            reasons.append("+ existing footage captions signal")

    return score, reasons


def cmd_list(_args: argparse.Namespace) -> None:
    recipes = load_all_recipes()
    rows = []
    for recipe_id in sorted(recipes):
        recipe = recipes[recipe_id]
        rows.append(
            {
                "id": recipe_id,
                "name": recipe["name"],
                "target_seconds": recipe["duration_seconds"]["target"],
                "aspect_ratios": recipe["aspect_ratios"],
                "stages": len(recipe["stages"]),
            }
        )
    emit(
        {
            "status": "succeeded",
            "stage": "list_recipes",
            "recipes": rows,
            "recipe_count": len(rows),
        }
    )


def cmd_show(args: argparse.Namespace) -> None:
    recipes = load_all_recipes()
    recipe = recipes.get(args.recipe_id)
    if not recipe:
        emit(
            {
                "status": "failed",
                "error": f"Unknown recipe: {args.recipe_id}",
                "available": sorted(recipes),
            }
        )
        sys.exit(2)
    emit({"status": "succeeded", "stage": "show_recipe", "recipe": recipe})


def cmd_validate(_args: argparse.Namespace) -> None:
    report = validate_registry()
    if report["valid"]:
        emit(
            {
                "status": "succeeded",
                "stage": "validate_recipes",
                "recipe_count": report["recipe_count"],
                "recipe_ids": report["recipe_ids"],
            }
        )
        return
    emit(
        {
            "status": "failed",
            "stage": "validate_recipes",
            "errors": report["errors"],
            "recipe_ids": report["recipe_ids"],
        }
    )
    sys.exit(2)


def cmd_match(args: argparse.Namespace) -> None:
    recipes = load_all_recipes()
    scored = []
    for recipe_id, recipe in recipes.items():
        score, reasons = score_recipe(recipe, args.goal)
        scored.append(
            {
                "recipe_id": recipe_id,
                "name": recipe["name"],
                "score": score,
                "reasons": reasons,
            }
        )
    scored.sort(key=lambda row: row["score"], reverse=True)
    best = scored[0]
    emit(
        {
            "status": "succeeded",
            "stage": "match_recipe",
            "goal": args.goal,
            "best_match": best,
            "ranking": scored,
        }
    )


def cmd_plan(args: argparse.Namespace) -> None:
    recipes = load_all_recipes()
    recipe = recipes.get(args.recipe)
    if not recipe:
        emit({"status": "failed", "error": f"Unknown recipe: {args.recipe}"})
        sys.exit(2)

    plan = {
        "recipe_id": recipe["id"],
        "goal": args.goal,
        "target_duration_seconds": recipe["duration_seconds"]["target"],
        "aspect_ratios": recipe["aspect_ratios"],
        "deliverables": recipe["deliverables"],
        "stages": [
            {
                "id": stage["id"],
                "title": stage["title"],
                "paid_generation": stage.get("paid_generation", False),
                "artifacts": stage.get("artifacts", []),
                "actions": stage["actions"],
            }
            for stage in recipe["stages"]
        ],
        "paid_stages": [
            stage["id"]
            for stage in recipe["stages"]
            if stage.get("paid_generation")
        ],
    }
    emit({"status": "succeeded", "stage": "plan_recipe", "plan": plan})


def cmd_test(_args: argparse.Namespace) -> None:
    report = validate_registry()
    recipes = load_all_recipes()
    tests = []

    tests.append(
        {
            "name": "schema_file_exists",
            "passed": SCHEMA_PATH.exists(),
        }
    )
    tests.append(
        {
            "name": "minimum_recipe_count",
            "passed": report["recipe_count"] >= 8,
            "detail": report["recipe_count"],
        }
    )
    tests.append(
        {
            "name": "registry_valid",
            "passed": report["valid"],
            "errors": report["errors"],
        }
    )

    for recipe_id in sorted(recipes):
        recipe = recipes[recipe_id]
        tests.append(
            {
                "name": f"stages_{recipe_id}",
                "passed": len(recipe["stages"]) >= 3,
            }
        )
        tests.append(
            {
                "name": f"keywords_{recipe_id}",
                "passed": len(recipe.get("routing_keywords", [])) >= 3,
            }
        )

    match_cases = [
        ("TikTok ad for waitlist signups", "ugc-ai-ad"),
        ("90 second news explainer with source proof", "avatar-explainer"),
        ("repurpose my podcast into shorts", "longform-repurpose"),
        ("SaaS product demo walkthrough", "screencast-demo"),
        ("browser proof of the announcement", "agent-browser-proof"),
    ]
    for goal, expected in match_cases:
        scored = [
            (rid, score_recipe(recipes[rid], goal)[0])
            for rid in recipes
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        winner = scored[0][0]
        tests.append(
            {
                "name": f"match_{expected}",
                "passed": winner == expected,
                "goal": goal,
                "winner": winner,
            }
        )

    failed = [t for t in tests if not t["passed"]]
    emit(
        {
            "status": "succeeded" if not failed else "failed",
            "stage": "test_recipes",
            "tests_run": len(tests),
            "tests_failed": len(failed),
            "failures": failed,
            "recipe_ids": report["recipe_ids"],
        }
    )
    if failed:
        sys.exit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Super Video Maker recipe registry")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list").set_defaults(func=cmd_list)

    show = sub.add_parser("show")
    show.add_argument("recipe_id")
    show.set_defaults(func=cmd_show)

    sub.add_parser("validate").set_defaults(func=cmd_validate)

    match = sub.add_parser("match")
    match.add_argument("--goal", required=True)
    match.set_defaults(func=cmd_match)

    plan = sub.add_parser("plan")
    plan.add_argument("--recipe", required=True)
    plan.add_argument("--goal", default="")
    plan.set_defaults(func=cmd_plan)

    sub.add_parser("test").set_defaults(func=cmd_test)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

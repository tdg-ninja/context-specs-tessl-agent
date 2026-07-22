#!/usr/bin/env python3
"""List skills affected by a git range and optionally require eval coverage."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def run(args: list[str]) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()


def ref_exists(ref: str) -> bool:
    try:
        run(["git", "rev-parse", "--verify", ref])
        return True
    except subprocess.CalledProcessError:
        return False


def changed_skill_names(base: str, head: str) -> set[str]:
    if not ref_exists(base):
        base = "HEAD~1"
    diff = run(["git", "diff", "--name-only", f"{base}...{head}", "--", "skills/"])
    return {line.split("/", 2)[1] for line in diff.splitlines() if line.startswith("skills/") and len(line.split("/")) >= 2}


def new_skill_names(base: str, head: str) -> set[str]:
    if not ref_exists(base):
        base = "HEAD~1"
    diff = run(["git", "diff", "--name-status", f"{base}...{head}", "--", "skills/"])
    names: set[str] = set()
    for line in diff.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0], parts[1]
        if status.startswith("A") and path.startswith("skills/") and path.endswith("/SKILL.md"):
            names.add(path.split("/", 2)[1])
    return names


def all_skill_names() -> set[str]:
    return {p.parent.name for p in Path("skills").glob("*/SKILL.md")}


def has_eval_coverage(skill: str) -> bool:
    eval_root = Path("evals")
    if not eval_root.exists():
        return False
    normalized = skill.replace("-", " ").lower()
    for scenario in eval_root.iterdir():
        if not scenario.is_dir():
            continue
        if skill in scenario.name:
            return True
        text = "\n".join(p.read_text(errors="ignore") for p in scenario.glob("*.md"))
        text += "\n" + "\n".join(p.read_text(errors="ignore") for p in scenario.glob("*.json"))
        lowered = text.lower().replace("-", " ")
        if normalized in lowered or skill.lower() in text.lower():
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--mode", choices=["changed", "new", "all"], default="changed")
    parser.add_argument("--format", choices=["lines", "json", "csv"], default="lines")
    parser.add_argument("--require-evals", action="store_true")
    args = parser.parse_args()

    if args.mode == "all":
        skills = all_skill_names()
    elif args.mode == "new":
        skills = new_skill_names(args.base, args.head)
    else:
        skills = changed_skill_names(args.base, args.head)
    skills = {skill for skill in skills if Path("skills", skill, "SKILL.md").exists()}

    missing_evals = sorted(skill for skill in skills if not has_eval_coverage(skill)) if args.require_evals else []
    result = {"skills": sorted(skills), "missingEvalCoverage": missing_evals}

    if args.format == "json":
        print(json.dumps(result, indent=2))
    elif args.format == "csv":
        print(",".join(result["skills"]))
    else:
        for skill in result["skills"]:
            print(skill)

    if missing_evals:
        print("Skills missing eval coverage: " + ", ".join(missing_evals), file=__import__("sys").stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

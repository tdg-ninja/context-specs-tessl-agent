#!/usr/bin/env python3
"""Write a PR-friendly summary of Tessl skill quality review scores."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any


def changed_skills(base_ref: str) -> list[str]:
    try:
        subprocess.run(["git", "rev-parse", "--verify", base_ref], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        base_ref = "HEAD~1"
    diff = subprocess.check_output(["git", "diff", "--name-only", f"{base_ref}...HEAD", "--", "skills/"], text=True)
    skills = sorted({line.split("/", 2)[1] for line in diff.splitlines() if line.startswith("skills/") and len(line.split("/")) >= 2})
    return [skill for skill in skills if Path("skills", skill, "SKILL.md").exists()]


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--out", default=".tessl/review-results/skill-quality-summary.md")
    parser.add_argument("--min-score", type=int, default=int(os.environ.get("MIN_REVIEW_SCORE", "70")))
    args = parser.parse_args()

    skills = changed_skills(args.base_ref)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "<!-- tessl-skill-quality -->",
        "## Tessl skill quality review",
        "",
        f"Minimum score: **{args.min_score}%**",
        "",
    ]

    if not skills:
        lines.extend([
            "No changed skills were detected in this PR.",
            "",
            "This summary is produced by `tessl review run quality` only when skill files change.",
        ])
        out.write_text("\n".join(lines).rstrip() + "\n")
        print(out)
        return 0

    lines.append("| Skill | Score | Review run | Status |")
    lines.append("|---|---:|---|---|")
    failures = 0
    for skill in skills:
        review = load_json(Path("catalog", "reviews", f"skills__{skill}.json")) or {}
        score = review.get("score")
        run_id = review.get("reviewRunId") or "missing"
        status = review.get("status") or "missing"
        score_text = f"{score}%" if isinstance(score, int) else "missing"
        run_text = f"`{run_id}`" if run_id != "missing" else "missing"
        ok = status == "reviewed" and isinstance(score, int) and score >= args.min_score and run_id != "missing"
        if not ok:
            failures += 1
        icon = "✅" if ok else "⚠️"
        lines.append(f"| `{skill}` | {score_text} | {run_text} | {icon} {status} |")

    lines.extend([
        "",
        "Review provenance is committed under `catalog/reviews/`; each score is tied to the reviewed artifact digest.",
        "",
        "**What is Tessl here:** `tessl review run quality` scores changed skills and `tessl plugin lint` validates plugin packaging.",
    ])

    out.write_text("\n".join(lines).rstrip() + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

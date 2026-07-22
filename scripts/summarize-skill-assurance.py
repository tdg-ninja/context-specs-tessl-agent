#!/usr/bin/env python3
"""Write a PR-friendly summary of Tessl skill assurance results."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


def run(args: list[str]) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()


def ref_exists(ref: str) -> bool:
    try:
        run(["git", "rev-parse", "--verify", ref])
        return True
    except subprocess.CalledProcessError:
        return False


def changed_skills(base: str, head: str = "HEAD") -> list[str]:
    if not ref_exists(base):
        base = "HEAD~1"
    diff = run(["git", "diff", "--name-only", f"{base}...{head}", "--", "skills/"])
    return sorted({
        line.split("/", 2)[1]
        for line in diff.splitlines()
        if line.startswith("skills/") and len(line.split("/")) >= 2 and Path("skills", line.split("/", 2)[1], "SKILL.md").exists()
    })


def new_skills(base: str, head: str = "HEAD") -> list[str]:
    if not ref_exists(base):
        base = "HEAD~1"
    diff = run(["git", "diff", "--name-status", f"{base}...{head}", "--", "skills/"])
    names: set[str] = set()
    for line in diff.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].startswith("A") and parts[1].startswith("skills/") and parts[1].endswith("/SKILL.md"):
            names.add(parts[1].split("/", 2)[1])
    return sorted(name for name in names if Path("skills", name, "SKILL.md").exists())


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return None


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
        text = "\n".join(p.read_text(errors="ignore") for p in list(scenario.glob("*.md")) + list(scenario.glob("*.json")))
        lowered = text.lower().replace("-", " ")
        if normalized in lowered or skill.lower() in text.lower():
            return True
    return False


def security_summary(skill: str) -> str:
    json_path = Path(".tessl/security-results") / f"{skill}.json"
    txt_path = Path(".tessl/security-results") / f"{skill}.txt"
    data = read_json(json_path)
    if data:
        status = data.get("status") or data.get("review", {}).get("status") or "complete"
        run_id = data.get("reviewRunId") or data.get("id") or "see artifact"
        highest = data.get("highestSeverity") or data.get("severity") or data.get("review", {}).get("highestSeverity")
        suffix = f", highest: {highest}" if highest else ""
        return f"✅ {status} (`{run_id}`{suffix})"
    if txt_path.exists():
        text = txt_path.read_text(errors="ignore")
        if "Review complete" in text or "Overall:" in text or "Security" in text:
            m = re.search(r"Review run started:\s*([a-zA-Z0-9-]+)", text)
            run = f" `{m.group(1)}`" if m else ""
            return f"✅ completed{run}"
        return "⚠️ see security artifact"
    return "not run"


def eval_summary(skill: str) -> str:
    coverage = "coverage ✅" if has_eval_coverage(skill) else "coverage ⚠️ missing"
    run_json = Path(".tessl/eval-results") / f"{skill}-run.json"
    lint_txt = Path(".tessl/eval-results") / f"{skill}-lint.txt"
    if run_json.exists():
        data = read_json(run_json)
        run_id = None
        if isinstance(data, dict):
            run_id = data.get("evalRunId") or data.get("id") or data.get("runId")
        return f"{coverage}; run ✅" + (f" (`{run_id}`)" if run_id else "")
    if lint_txt.exists():
        return f"{coverage}; lint ✅; remote run skipped"
    return coverage + "; not run"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", default="origin/main")
    parser.add_argument("--out", default=".tessl/review-results/skill-assurance-summary.md")
    parser.add_argument("--min-score", type=int, default=70)
    args = parser.parse_args()

    changed = changed_skills(args.base_ref)
    added = set(new_skills(args.base_ref))
    skills = changed
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "<!-- tessl-skill-assurance -->",
        "## Tessl skill assurance",
        "",
        "This summarizes Tessl quality, security, and eval evidence for skill changes in this PR.",
        "",
    ]

    if not skills:
        lines.extend([
            "No changed skills were detected in this PR.",
            "",
            "- Quality review: not applicable",
            "- Security review: not applicable",
            "- Evals: not applicable",
        ])
    else:
        lines.append("| Skill | Change | Quality | Security | Evals |")
        lines.append("|---|---|---:|---|---|")
        for skill in skills:
            review = read_json(Path("catalog/reviews") / f"skills__{skill}.json") or {}
            score = review.get("score")
            run_id = review.get("reviewRunId")
            quality = f"{score}%" if isinstance(score, int) else "missing"
            if run_id:
                quality += f" (`{run_id}`)"
            quality += " ✅" if isinstance(score, int) and score >= args.min_score else " ⚠️"
            change = "new" if skill in added else "changed"
            lines.append(f"| `{skill}` | {change} | {quality} | {security_summary(skill)} | {eval_summary(skill)} |")
        lines.extend([
            "",
            "Full Tessl review, security, and eval artifacts are attached to the workflow run.",
            "Publishing remains gated by the Tessl publish workflows after these checks pass.",
        ])

    out.write_text("\n".join(lines).rstrip() + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

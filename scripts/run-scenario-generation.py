#!/usr/bin/env python3
"""Run an advisory Tessl scenario generation plan and write PR-friendly artifacts."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

OUT_DIR = Path(".tessl/scenario-generation")


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def clamp_count(value: Any) -> int:
    try:
        count = int(value)
    except Exception:
        count = 2
    return max(1, min(count, 5))


def run_command(cmd: list[str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plan = read_json(OUT_DIR / "plan.json")
    pr_number = os.environ.get("PR_NUMBER", "")
    repo = os.environ.get("REPO", "tdg-ninja/context-specs-tessl-agent")
    workspace = os.environ.get("TESSL_WORKSPACE", "cap1-context-specs")

    mode = str(plan.get("mode") or plan.get("source") or "plugin").lower()
    if mode not in {"plugin", "repo", "skip"}:
        mode = "plugin"
    count = clamp_count(plan.get("count", 2))
    reason = str(plan.get("reason") or "No reason provided by scenario generation planner.")

    summary = [
        "<!-- tessl-scenario-generation -->",
        "## Tessl eval scenario generation",
        "",
        f"- **Plan:** `{mode}`",
        f"- **Count:** `{count}`",
        f"- **Reason:** {reason}",
        "",
    ]

    if mode == "skip":
        summary.append("Scenario generation skipped by plan.")
        (OUT_DIR / "summary.md").write_text("\n".join(summary).rstrip() + "\n")
        print(OUT_DIR / "summary.md")
        return 0

    if mode == "repo" and pr_number:
        cmd = [
            "tessl",
            "scenario",
            "generate",
            repo,
            "--prs",
            pr_number,
            "--workspace",
            workspace,
            "--context",
            "skills/**/*.md,docs/**/*.md,.github/workflows/**/*.yml,tessl.json,verifiers/*.json",
            "--json",
        ]
    else:
        mode = "plugin"
        cmd = ["tessl", "scenario", "generate", ".", "--count", str(count), "--json"]

    (OUT_DIR / "command.txt").write_text(" ".join(cmd) + "\n")
    rc, output = run_command(cmd)
    (OUT_DIR / "scenario-generate-output.txt").write_text(output)

    generation_id = None
    try:
        data = json.loads(output)
        generation_id = data.get("id") or data.get("scenarioGenerationId") or data.get("generationId")
        (OUT_DIR / "scenario-generate.json").write_text(json.dumps(data, indent=2) + "\n")
    except Exception:
        data = None

    if rc == 0:
        summary.extend([
            "Scenario generation was started successfully.",
            f"- **Generation ID:** `{generation_id or 'see artifact'}`",
            f"- **Command:** `{ ' '.join(cmd) }`",
        ])
    else:
        summary.extend([
            "Scenario generation did not start successfully. This is advisory and does not block the PR.",
            f"- **Exit code:** `{rc}`",
            f"- **Command:** `{ ' '.join(cmd) }`",
            "- **Next action:** inspect the uploaded `scenario-generate-output.txt` artifact.",
        ])

    (OUT_DIR / "summary.md").write_text("\n".join(summary).rstrip() + "\n")
    print(OUT_DIR / "summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

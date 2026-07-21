#!/usr/bin/env python3
"""Validate that a GitHub issue is structured for Dark Factory dispatch."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

SECTION_ALIASES = {
    "goal": ["goal"],
    "scope": ["scope"],
    "acceptance criteria": ["acceptance criteria", "acceptance", "acceptance criterion"],
    "constraints": ["constraints", "constraint"],
}


def normalize_heading(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def extract_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    for line in body.splitlines():
        match = re.match(r"^#{2,6}\s+(.+?)\s*$", line)
        if match:
            if current:
                sections[current] = "\n".join(buf).strip()
            current = normalize_heading(match.group(1))
            buf = []
        elif current:
            buf.append(line)

    if current:
        sections[current] = "\n".join(buf).strip()
    return sections


def section_value(sections: dict[str, str], canonical: str) -> str:
    aliases = SECTION_ALIASES[canonical]
    for heading, value in sections.items():
        if heading in aliases:
            return value
    return ""


def has_list_item(text: str) -> bool:
    return any(re.match(r"^\s*(- \[[ xX]\]|[-*]\s+|\d+\.\s+)", line) for line in text.splitlines())


def labels(issue: dict[str, Any]) -> set[str]:
    return {label.get("name", "") for label in issue.get("labels", [])}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue-json", required=True)
    parser.add_argument("--trigger", required=True, choices=["label", "comment", "manual"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--dispatch-label", default="dark-factory")
    args = parser.parse_args()

    issue = json.loads(Path(args.issue_json).read_text())
    body = issue.get("body") or ""
    sections = extract_sections(body)
    failures: list[str] = []

    if not (issue.get("title") or "").strip():
        failures.append("Issue title is empty.")

    goal = section_value(sections, "goal")
    if len(goal.strip()) < 20:
        failures.append("Missing or too-short `## Goal` section.")

    scope = section_value(sections, "scope")
    if len(scope.strip()) < 10:
        failures.append("Missing or too-short `## Scope` section.")

    acceptance = section_value(sections, "acceptance criteria")
    if len(acceptance.strip()) < 5 or not has_list_item(acceptance):
        failures.append("`## Acceptance criteria` must contain at least one checkbox, bullet, or numbered item.")

    constraints = section_value(sections, "constraints")
    if len(constraints.strip()) < 5:
        failures.append("Missing `## Constraints` section. Use `None` only when there are truly no constraints.")

    if args.trigger == "label" and args.dispatch_label not in labels(issue):
        failures.append(f"Issue-triggered dispatch requires the `{args.dispatch_label}` label.")

    valid = not failures
    report = [
        "# Dark Factory issue structure validation",
        "",
        f"- **Issue:** #{issue.get('number')} — {issue.get('title')}",
        f"- **Trigger:** {args.trigger}",
        f"- **Valid:** {'yes' if valid else 'no'}",
        "",
    ]
    if failures:
        report.append("## Missing or invalid fields")
        report.extend(f"- {failure}" for failure in failures)
        report.append("")
        report.append("## Required issue shape")
        report.append("Use `docs/github-issue-contract.md` or the **Dark Factory task** issue template.")
    else:
        report.append("All required sections are present and dispatchable.")

    Path(args.output).write_text("\n".join(report).rstrip() + "\n")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"valid={'true' if valid else 'false'}\n")

    print("\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

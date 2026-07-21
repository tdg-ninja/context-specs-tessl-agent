#!/usr/bin/env python3
"""Collect bounded GitHub evidence for the Dark Factory learning loop."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_date(days: int) -> str:
    return (utc_now() - timedelta(days=days)).date().isoformat()


def run_gh_json(args: list[str], missing: list[str], label: str) -> Any:
    command = ["gh", "api", "--method", "GET", *args]
    try:
        result = subprocess.run(command, check=True, text=True, capture_output=True)
    except FileNotFoundError:
        missing.append(f"{label}: GitHub CLI `gh` is not installed.")
        return None
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or str(exc)).strip()
        missing.append(f"{label}: `{' '.join(command)}` failed: {message}")
        return None

    try:
        return json.loads(result.stdout or "null")
    except json.JSONDecodeError as exc:
        missing.append(f"{label}: GitHub API returned non-JSON output: {exc}")
        return None


def gh_get(path: str, missing: list[str], label: str, **params: str) -> Any:
    args = [path]
    for key, value in params.items():
        args.extend(["-f", f"{key}={value}"])
    return run_gh_json(args, missing, label)


def search_issues(repo: str, query: str, missing: list[str], label: str, limit: int) -> list[dict[str, Any]]:
    data = gh_get("search/issues", missing, label, q=f"repo:{repo} {query}", per_page=str(limit))
    if not isinstance(data, dict):
        return []
    items = data.get("items", [])
    return items if isinstance(items, list) else []


def pull_number(item: dict[str, Any]) -> int | None:
    number = item.get("number")
    return number if isinstance(number, int) else None


def summarize_user(user: dict[str, Any] | None) -> str | None:
    if not isinstance(user, dict):
        return None
    return user.get("login")


def summarize_labels(labels: list[dict[str, Any]] | None) -> list[str]:
    if not isinstance(labels, list):
        return []
    names: list[str] = []
    for label in labels:
        if isinstance(label, dict) and isinstance(label.get("name"), str):
            names.append(label["name"])
    return names


def collect_pr_details(repo: str, numbers: list[int], missing: list[str], limit: int) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for number in numbers[:limit]:
        pull = gh_get(f"repos/{repo}/pulls/{number}", missing, f"pull #{number}")
        files = gh_get(f"repos/{repo}/pulls/{number}/files", missing, f"pull #{number} files", per_page="100")
        reviews = gh_get(f"repos/{repo}/pulls/{number}/reviews", missing, f"pull #{number} reviews", per_page="100")
        comments = gh_get(f"repos/{repo}/issues/{number}/comments", missing, f"pull #{number} issue comments", per_page="100")

        if not isinstance(pull, dict):
            continue
        details.append(
            {
                "number": number,
                "title": pull.get("title"),
                "url": pull.get("html_url"),
                "state": pull.get("state"),
                "merged": pull.get("merged"),
                "merged_at": pull.get("merged_at"),
                "closed_at": pull.get("closed_at"),
                "author": summarize_user(pull.get("user")),
                "labels": summarize_labels(pull.get("labels")),
                "additions": pull.get("additions"),
                "deletions": pull.get("deletions"),
                "changed_files": pull.get("changed_files"),
                "files": [
                    {
                        "filename": f.get("filename"),
                        "status": f.get("status"),
                        "additions": f.get("additions"),
                        "deletions": f.get("deletions"),
                    }
                    for f in (files if isinstance(files, list) else [])
                ],
                "reviews": [
                    {
                        "user": summarize_user(r.get("user")),
                        "state": r.get("state"),
                        "submitted_at": r.get("submitted_at"),
                        "body": (r.get("body") or "")[:2000],
                    }
                    for r in (reviews if isinstance(reviews, list) else [])
                ],
                "comments": [
                    {
                        "user": summarize_user(c.get("user")),
                        "created_at": c.get("created_at"),
                        "body": (c.get("body") or "")[:2000],
                    }
                    for c in (comments if isinstance(comments, list) else [])
                ],
            }
        )
    return details


def collect_runs(repo: str, since: str, missing: list[str]) -> list[dict[str, Any]]:
    data = gh_get(
        f"repos/{repo}/actions/runs",
        missing,
        "workflow runs",
        per_page="100",
        status="completed",
        created=f">={since}",
    )
    runs = data.get("workflow_runs", []) if isinstance(data, dict) else []
    if not isinstance(runs, list):
        return []

    failures: list[dict[str, Any]] = []
    for run in runs:
        if run.get("conclusion") not in {"failure", "timed_out", "cancelled", "startup_failure"}:
            continue
        if str(run.get("created_at", ""))[:10] < since:
            continue
        jobs = gh_get(
            f"repos/{repo}/actions/runs/{run.get('id')}/jobs",
            missing,
            f"workflow run {run.get('id')} jobs",
            per_page="100",
        )
        failures.append(
            {
                "id": run.get("id"),
                "name": run.get("name"),
                "event": run.get("event"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "created_at": run.get("created_at"),
                "updated_at": run.get("updated_at"),
                "url": run.get("html_url"),
                "head_branch": run.get("head_branch"),
                "head_sha": run.get("head_sha"),
                "pull_requests": run.get("pull_requests", []),
                "jobs": [
                    {
                        "name": job.get("name"),
                        "status": job.get("status"),
                        "conclusion": job.get("conclusion"),
                        "started_at": job.get("started_at"),
                        "completed_at": job.get("completed_at"),
                        "steps": [
                            {
                                "name": step.get("name"),
                                "status": step.get("status"),
                                "conclusion": step.get("conclusion"),
                            }
                            for step in job.get("steps", [])
                            if isinstance(step, dict) and step.get("conclusion") not in {"success", "skipped", None}
                        ],
                    }
                    for job in (jobs.get("jobs", []) if isinstance(jobs, dict) else [])
                ],
            }
        )
    return failures


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--lookback-days", type=int, default=14)
    parser.add_argument("--output-dir", default=".tessl/dark-factory/learning")
    parser.add_argument("--detail-limit", type=int, default=20)
    args = parser.parse_args()

    if not args.repo or "/" not in args.repo:
        raise SystemExit("--repo or GITHUB_REPOSITORY must be set to owner/repo")

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    missing: list[str] = []
    since = iso_date(args.lookback_days)

    merged_items = search_issues(args.repo, f"is:pr is:merged merged:>={since}", missing, "merged PR search", 50)
    closed_items = search_issues(args.repo, f"is:pr is:closed -is:merged closed:>={since}", missing, "closed unmerged PR search", 50)
    dark_factory_items = search_issues(args.repo, f"label:dark-factory updated:>={since}", missing, "Dark Factory activity search", 50)

    merged_prs = collect_pr_details(args.repo, [n for item in merged_items if (n := pull_number(item))], missing, args.detail_limit)
    closed_unmerged_prs = collect_pr_details(args.repo, [n for item in closed_items if (n := pull_number(item))], missing, args.detail_limit)
    failed_runs = collect_runs(args.repo, since, missing)

    dark_factory_activity = [
        {
            "number": item.get("number"),
            "title": item.get("title"),
            "url": item.get("html_url"),
            "state": item.get("state"),
            "updated_at": item.get("updated_at"),
            "closed_at": item.get("closed_at"),
            "author": summarize_user(item.get("user")),
            "labels": summarize_labels(item.get("labels")),
            "is_pull_request": "pull_request" in item,
            "body": (item.get("body") or "")[:2000],
        }
        for item in dark_factory_items
    ]

    metadata = {
        "repo": args.repo,
        "generated_at": utc_now().isoformat(),
        "lookback_days": args.lookback_days,
        "since": since,
        "detail_limit": args.detail_limit,
        "partial": bool(missing),
    }

    write_json(out / "metadata.json", metadata)
    write_json(out / "merged-prs.json", merged_prs)
    write_json(out / "closed-unmerged-prs.json", closed_unmerged_prs)
    write_json(out / "failed-runs.json", failed_runs)
    write_json(out / "dark-factory-activity.json", dark_factory_activity)
    write_json(out / "missing-data.json", missing)

    summary = [
        "# Dark Factory learning evidence summary",
        "",
        f"- Repository: `{args.repo}`",
        f"- Generated at: `{metadata['generated_at']}`",
        f"- Lookback: {args.lookback_days} days, since `{since}`",
        f"- Merged PRs with detail: {len(merged_prs)}",
        f"- Closed-without-merge PRs with detail: {len(closed_unmerged_prs)}",
        f"- Failed/timed-out/cancelled workflow runs: {len(failed_runs)}",
        f"- Dark Factory issues/PRs updated: {len(dark_factory_activity)}",
        f"- Partial collection: {'yes' if missing else 'no'}",
        "",
    ]
    if missing:
        summary.append("## Missing or partial data")
        summary.extend(f"- {entry}" for entry in missing)
        summary.append("")
    summary.append("## Evidence files")
    for name in ["metadata.json", "merged-prs.json", "closed-unmerged-prs.json", "failed-runs.json", "dark-factory-activity.json", "missing-data.json"]:
        summary.append(f"- `{out / name}`")
    (out / "evidence-summary.md").write_text("\n".join(summary).rstrip() + "\n")

    print("\n".join(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

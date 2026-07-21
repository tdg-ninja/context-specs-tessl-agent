#!/usr/bin/env python3
"""Validate Context Specs skill review records and generated catalog state."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def digest_entries(entries: list[dict[str, str]]) -> str:
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def artifact_digest(path: Path, root: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    entries = [
        {"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p)}
        for p in sorted(path.rglob("*"))
        if p.is_file()
    ]
    return digest_entries(entries)


def review_file_for(root: Path, artifact: Path) -> Path:
    rel = artifact.relative_to(root).as_posix()
    return root / "catalog" / "reviews" / f"{rel.replace('/', '__')}.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--min-score", type=int, default=70)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    failures: list[str] = []

    artifacts = [p for p in sorted((root / "skills").iterdir()) if (p / "SKILL.md").exists()]
    artifacts.extend(sorted((root / "subagents").glob("*.md")))

    for artifact in artifacts:
        rel = artifact.relative_to(root).as_posix()
        review_path = review_file_for(root, artifact)
        if not review_path.exists():
            failures.append(f"{rel}: missing {review_path.relative_to(root)}")
            continue
        try:
            review = json.loads(review_path.read_text())
        except json.JSONDecodeError as exc:
            failures.append(f"{rel}: invalid review JSON: {exc}")
            continue

        digest = artifact_digest(artifact, root)
        if review.get("artifact") != rel:
            failures.append(f"{rel}: review artifact is {review.get('artifact')!r}")
        if review.get("sha256") != digest:
            failures.append(f"{rel}: review digest is stale")
        if review.get("status") != "reviewed":
            failures.append(f"{rel}: status is {review.get('status')!r}")
        if artifact.is_dir():
            score = review.get("score")
            if not isinstance(score, int) or score < args.min_score:
                failures.append(f"{rel}: score {score!r} is below {args.min_score}")
            if not review.get("reviewRunId"):
                failures.append(f"{rel}: missing Tessl reviewRunId")
            if "tessl/" not in str(review.get("reviewer", "")):
                failures.append(f"{rel}: reviewer should identify the Tessl review plugin")

    if failures:
        print("Review record check failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"Review record check passed for {len(artifacts)} artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

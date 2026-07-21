#!/usr/bin/env python3
"""Update one catalog/reviews record from a completed Tessl review run JSON file."""
from __future__ import annotations

import argparse
import hashlib
import json
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


def skill_digest(skill_dir: Path, root: Path) -> str:
    entries = [
        {"path": p.relative_to(root).as_posix(), "sha256": sha256_file(p)}
        for p in sorted(skill_dir.rglob("*"))
        if p.is_file()
    ]
    return digest_entries(entries)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--skill", required=True, help="Skill name or path under skills/")
    parser.add_argument("--review-json", required=True, help="Path produced by `tessl review view --json <id>`")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skill_dir = Path(args.skill)
    if not skill_dir.is_absolute():
        skill_dir = root / (args.skill if args.skill.startswith("skills/") else f"skills/{args.skill}")
    if not (skill_dir / "SKILL.md").exists():
        raise SystemExit(f"Skill not found: {skill_dir}")

    review = json.loads(Path(args.review_json).read_text())
    review_id = review.get("reviewRunId")
    status = review.get("status", "completed")
    score = review.get("review", {}).get("reviewScore")
    if status not in ("completed", None):
        raise SystemExit(f"Review {review_id} is not complete: {status}")
    if not isinstance(score, int):
        raise SystemExit(f"Review {review_id} has no integer review.reviewScore")

    rel = skill_dir.relative_to(root).as_posix()
    record = {
        "schemaVersion": 1,
        "artifact": rel,
        "sha256": skill_digest(skill_dir, root),
        "status": "reviewed",
        "reviewer": review.get("review-plugin", "tessl/default-skill-review@0.1.0"),
        "reviewRunId": review_id,
        "score": score,
        "reviewedAt": review.get("createdAt") or review.get("updatedAt") or "see reviewRunId",
        "notes": "Reviewed with tessl review run quality in workspace cap1-context-specs before private registry publish.",
    }

    out = root / "catalog" / "reviews" / f"{rel.replace('/', '__')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=2) + "\n")
    print(f"Updated {out.relative_to(root)} with score {score} from {review_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

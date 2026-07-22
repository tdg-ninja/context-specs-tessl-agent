#!/usr/bin/env python3
"""Create or update a PR comment identified by a hidden marker."""
from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request


def request(method: str, url: str, token: str, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--pr", required=True)
    parser.add_argument("--body-file", required=True)
    parser.add_argument("--marker", required=True)
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GH_TOKEN or GITHUB_TOKEN is required")

    body = open(args.body_file, encoding="utf-8").read()
    if args.marker not in body:
        body = f"{args.marker}\n{body}"

    owner_repo = args.repo
    comments_url = f"https://api.github.com/repos/{owner_repo}/issues/{args.pr}/comments"
    comments = request("GET", comments_url, token)
    existing = next((c for c in comments if args.marker in (c.get("body") or "")), None)
    if existing:
        request("PATCH", existing["url"], token, {"body": body})
        print(f"Updated PR comment {existing['id']}")
    else:
        created = request("POST", comments_url, token, {"body": body})
        print(f"Created PR comment {created['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

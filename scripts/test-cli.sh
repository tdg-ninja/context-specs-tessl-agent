#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 "$ROOT/bin/context-specs.py" catalog generate --source "$ROOT" --out "$TMP/catalog.json" >/dev/null
python3 "$ROOT/bin/context-specs.py" install --source "$ROOT" --target "$TMP/project" >/dev/null
python3 "$ROOT/bin/context-specs.py" verify --target "$TMP/project" >/dev/null

test -f "$TMP/project/.claude/skills/spec-planning/SKILL.md"
test -f "$TMP/project/.claude/agents/slice-implementer.md"
test -f "$TMP/project/.context-specs/manifest.json"

echo "CLI smoke test passed"

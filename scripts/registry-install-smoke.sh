#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

python3 "$ROOT/bin/context-specs.py" install \
  --target "$TMP/project" \
  --plugin "${CONTEXT_SPECS_PLUGIN:-cap1-context-specs/context-specs}" \
  --version "${CONTEXT_SPECS_VERSION:-0.1.0}" \
  --agent "${CONTEXT_SPECS_AGENT:-claude-code}"

python3 "$ROOT/bin/context-specs.py" verify --target "$TMP/project"

test -f "$TMP/project/.tessl/plugins/cap1-context-specs/context-specs/skills/spec-planning/SKILL.md"
test -f "$TMP/project/.claude/skills/spec-planning/SKILL.md"
test -f "$TMP/project/.claude/agents/slice-implementer.md"
test -f "$TMP/project/.context-specs/manifest.json"

echo "Registry install smoke test passed"

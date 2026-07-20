#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${CONTEXT_SPECS_REPO_URL:-https://github.com/capitalone/context-specs.git}"
REF="${CONTEXT_SPECS_REF:-main}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd || pwd)"
if [ -f "$SCRIPT_DIR/bin/context-specs.py" ]; then
  exec python3 "$SCRIPT_DIR/bin/context-specs.py" install "$@"
fi

if command -v context-specs >/dev/null 2>&1; then
  exec context-specs install --source "$REPO_URL" --ref "$REF" "$@"
fi

TEMP_DIR=""
cleanup() {
  if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT

TEMP_DIR="$(mktemp -d)"
git clone --depth 1 --branch "$REF" --quiet "$REPO_URL" "$TEMP_DIR"
python3 "$TEMP_DIR/bin/context-specs.py" install --source "$TEMP_DIR" "$@"

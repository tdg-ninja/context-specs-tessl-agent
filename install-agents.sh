#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/capitalone/context-specs.git"
TEMP_DIR=""

cleanup() {
  if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT

echo "Installing context-specs agents..."

# Clone into a temp directory
TEMP_DIR="$(mktemp -d)"
git clone --depth 1 --quiet "$REPO_URL" "$TEMP_DIR"

# Verify source agents exist
SOURCE_DIR="$TEMP_DIR/subagents"
if [ ! -d "$SOURCE_DIR" ]; then
  echo "Error: No subagents/ directory found in the repository." >&2
  exit 1
fi

# Create target directory
mkdir -p .claude/agents

# Copy agent definitions
INSTALLED=()
for file in "$SOURCE_DIR"/*.md; do
  [ -f "$file" ] || continue
  cp "$file" ".claude/agents/$(basename "$file")"
  INSTALLED+=("$(basename "$file")")
done

if [ ${#INSTALLED[@]} -eq 0 ]; then
  echo "No agent definitions found to install."
  exit 0
fi

echo ""
echo "Installed ${#INSTALLED[@]} agent(s) into .claude/agents/:"
for name in "${INSTALLED[@]}"; do
  echo "  - $name"
done
echo ""
echo "Done."

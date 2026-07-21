#!/usr/bin/env bash
# check-agents-md.sh — mechanical freshness gate for the project's eager memory.
#
# AGENTS.md files rot: pointers go stale, files they reference get moved, and they
# quietly grow past the point of usefulness. This lint makes those failures loud.
# Wire it into scripts/local-checks.sh (and CI) so a stale map fails the build.
#
# Checks, for every AGENTS.md in the repo:
#   1. Line-count cap (root <= ROOT_CAP, nested <= NESTED_CAP).
#   2. Referenced repo paths exist (backtick `path/like/this` and [text](path) links
#      that look like in-repo paths).
#
# Exit 0 = clean. Exit 1 = at least one violation (with a remediation message).
#
# Caps are tweakable via env; defaults match routing-rules.md.

set -euo pipefail

ROOT_CAP="${AGENTS_MD_ROOT_CAP:-150}"
NESTED_CAP="${AGENTS_MD_NESTED_CAP:-80}"

fail=0
note() { echo "❌ $*" >&2; fail=1; }

# Find AGENTS.md files, skipping vendored/build dirs.
mapfile -t files < <(find . \
  -type d \( -name .git -o -name node_modules -o -name dist -o -name build -o -name target -o -name vendor \) -prune \
  -o -type f -name 'AGENTS.md' -print 2>/dev/null | sort)

if (( ${#files[@]} == 0 )); then
  echo "no AGENTS.md found (nothing to check)"
  exit 0
fi

for f in "${files[@]}"; do
  dir="$(dirname "$f")"

  # 1. Line-count cap. Root (./AGENTS.md) uses ROOT_CAP; nested use NESTED_CAP.
  lines=$(wc -l < "$f")
  if [[ "$f" == "./AGENTS.md" ]]; then cap="$ROOT_CAP"; else cap="$NESTED_CAP"; fi
  if (( lines > cap )); then
    note "$f is $lines lines (cap $cap). AGENTS.md is a map, not an encyclopedia —
       move detail into the Expert (.claude/skills/expert/) and leave a pointer."
  fi

  # 2. Referenced paths exist. Pull backticked tokens and markdown link targets
  #    that look like repo paths (contain a slash or a known dotfile/.md name).
  #    Resolve relative to the AGENTS.md's own directory, then to repo root.
  while IFS= read -r ref; do
    [[ -z "$ref" ]] && continue
    # Skip URLs, anchors, globs, and placeholder tokens like <feature>.
    [[ "$ref" =~ ^https?:// ]] && continue
    [[ "$ref" == \#* ]] && continue
    [[ "$ref" == *"<"* || "$ref" == *"*"* ]] && continue
    if [[ -e "$dir/$ref" || -e "$ref" ]]; then continue; fi
    note "$f references missing path: '$ref' — update the pointer or restore the file."
  done < <(grep -oE '`[^`]+`|\]\([^)]+\)' "$f" \
            | sed -E 's/^`//; s/`$//; s/^\]\(//; s/\)$//' \
            | grep -E '/|\.md$|\.sh$|^AGENTS\.md$' || true)
done

if (( fail )); then
  echo "check-agents-md: FAIL" >&2
  exit 1
fi
echo "check-agents-md: OK (${#files[@]} file(s))"

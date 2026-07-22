#!/usr/bin/env bash
set -euo pipefail

BASE_REF="${BASE_REF:-origin/main}"
HEAD_REF="${HEAD_REF:-HEAD}"
MODE="${SKILL_SCOPE:-changed}" # new | changed | all
WORKSPACE="${TESSL_WORKSPACE:-cap1-context-specs}"
FAIL_ON="${SECURITY_FAIL_ON:-high}"
LABEL_PREFIX="${SECURITY_LABEL_PREFIX:-skill-security}"

mkdir -p .tessl/security-results

case "$MODE" in
  all)
    mapfile_cmd=(python3 scripts/list-skills-for-assurance.py --mode all --format lines)
    ;;
  new)
    mapfile_cmd=(python3 scripts/list-skills-for-assurance.py --mode new --base "$BASE_REF" --head "$HEAD_REF" --format lines)
    ;;
  changed)
    mapfile_cmd=(python3 scripts/list-skills-for-assurance.py --mode changed --base "$BASE_REF" --head "$HEAD_REF" --format lines)
    ;;
  *)
    echo "Unsupported SKILL_SCOPE=$MODE; expected new, changed, or all" >&2
    exit 2
    ;;
esac

skills_file="$(mktemp)"
trap 'rm -f "$skills_file"' EXIT
"${mapfile_cmd[@]}" > "$skills_file"

if [ ! -s "$skills_file" ]; then
  echo "No skills selected for security review (scope=$MODE)."
  exit 0
fi

while IFS= read -r skill; do
  [ -n "$skill" ] || continue
  echo "::group::Tessl security review: $skill"
  tessl review run security \
    --workspace "$WORKSPACE" \
    --force \
    --fail-on "$FAIL_ON" \
    --label "${LABEL_PREFIX}-${skill}-${GITHUB_RUN_ID:-local}" \
    "skills/$skill" \
    | tee ".tessl/security-results/${skill}.txt"
  review_id="$(sed -n 's/.*Review run started: \([a-zA-Z0-9-]*\).*/\1/p' ".tessl/security-results/${skill}.txt" | tail -1)"
  if [ -n "$review_id" ]; then
    for _ in $(seq 1 60); do
      tessl review view --json "$review_id" > ".tessl/security-results/${skill}.json" || true
      if grep -q '"status"' ".tessl/security-results/${skill}.json"; then
        if ! grep -q '"status"[[:space:]]*:[[:space:]]*"incomplete"' ".tessl/security-results/${skill}.json"; then
          break
        fi
      fi
      sleep 10
    done
  fi
  echo "::endgroup::"
done < "$skills_file"

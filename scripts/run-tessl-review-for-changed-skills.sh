#!/usr/bin/env bash
set -euo pipefail

BASE_REF="${BASE_REF:-origin/main}"
WORKSPACE="${TESSL_WORKSPACE:-cap1-context-specs}"
MIN_SCORE="${MIN_REVIEW_SCORE:-70}"

if ! git rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  BASE_REF="HEAD~1"
fi

mapfile -t skills < <(
  git diff --name-only "$BASE_REF"...HEAD -- skills/ \
    | awk -F/ 'NF >= 2 && $1 == "skills" { print $2 }' \
    | sort -u
)

if [ "${#skills[@]}" -eq 0 ]; then
  echo "No changed skills detected relative to $BASE_REF."
  exit 0
fi

mkdir -p .tessl/review-results

for skill in "${skills[@]}"; do
  if [ ! -f "skills/$skill/SKILL.md" ]; then
    echo "Skipping removed or non-skill path: skills/$skill"
    continue
  fi

  echo "::group::Tessl quality review: $skill"
  echo "Running: tessl review run quality --workspace $WORKSPACE --threshold $MIN_SCORE --force skills/$skill"
  set +e
  output="$(tessl review run quality \
    --workspace "$WORKSPACE" \
    --threshold "$MIN_SCORE" \
    --force \
    --label "ci-${GITHUB_RUN_ID:-local}-$skill" \
    "skills/$skill" 2>&1)"
  rc=$?
  set -e
  echo "$output"
  review_id="$(printf '%s\n' "$output" | sed -n 's/.*Review run started: \([a-zA-Z0-9-]*\).*/\1/p' | tail -1)"

  if [ -n "$review_id" ]; then
    for _ in $(seq 1 60); do
      tessl review view --json "$review_id" > ".tessl/review-results/$skill.json" || true
      if grep -q '"reviewScore"' ".tessl/review-results/$skill.json"; then
        break
      fi
      sleep 10
    done
    cat ".tessl/review-results/$skill.json"
    python3 scripts/update-review-record.py --skill "$skill" --review-json ".tessl/review-results/$skill.json"
  fi

  if [ "$rc" -ne 0 ]; then
    echo "Tessl review failed for $skill with exit code $rc"
    exit "$rc"
  fi
  echo "::endgroup::"
done

python3 bin/context-specs.py catalog generate --source .
python3 scripts/check-review-records.py --root . --min-score "$MIN_SCORE"

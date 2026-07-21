#!/usr/bin/env bash
set -euo pipefail

BASE_REF="${BASE_REF:-origin/main}"
WORKSPACE="${TESSL_WORKSPACE:-cap1-context-specs}"
MIN_SCORE="${MIN_REVIEW_SCORE:-70}"

if ! git rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  BASE_REF="HEAD~1"
fi

skills_file="$(mktemp)"
trap 'rm -f "$skills_file"' EXIT

git diff --name-only "$BASE_REF"...HEAD -- skills/ \
  | awk -F/ 'NF >= 2 && $1 == "skills" { print $2 }' \
  | sort -u > "$skills_file"

skills=()
while IFS= read -r skill; do
  [ -n "$skill" ] && skills+=("$skill")
done < "$skills_file"

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

  if python3 - "$skill" "$MIN_SCORE" <<'PY'
import hashlib, json, sys
from pathlib import Path

skill = sys.argv[1]
min_score = int(sys.argv[2])
root = Path('.')
skill_dir = root / 'skills' / skill
review_path = root / 'catalog' / 'reviews' / f"skills__{skill}.json"

def sha256_file(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

entries = [
    {'path': p.as_posix(), 'sha256': sha256_file(p)}
    for p in sorted(skill_dir.rglob('*'))
    if p.is_file()
]
digest = hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
if not review_path.exists():
    sys.exit(1)
review = json.loads(review_path.read_text())
if review.get('sha256') != digest:
    sys.exit(1)
if review.get('status') != 'reviewed':
    sys.exit(1)
if not isinstance(review.get('score'), int) or review['score'] < min_score:
    sys.exit(1)
if not review.get('reviewRunId'):
    sys.exit(1)
sys.exit(0)
PY
  then
    echo "Existing Tessl review record for $skill is current and meets score threshold; skipping new review."
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

#!/usr/bin/env bash
set -euo pipefail

BASE_REF="${BASE_REF:-origin/main}"
HEAD_REF="${HEAD_REF:-HEAD}"
MODE="${SKILL_SCOPE:-changed}" # new | changed | all
LABEL_PREFIX="${EVAL_LABEL_PREFIX:-skill-eval}"
RUN_EVALS="${RUN_EVALS:-false}"
REQUIRE_EVALS="${REQUIRE_EVALS:-true}"

mkdir -p .tessl/eval-results

case "$MODE" in
  all)
    args=(--mode all --format lines)
    ;;
  new)
    args=(--mode new --base "$BASE_REF" --head "$HEAD_REF" --format lines)
    ;;
  changed)
    args=(--mode changed --base "$BASE_REF" --head "$HEAD_REF" --format lines)
    ;;
  *)
    echo "Unsupported SKILL_SCOPE=$MODE; expected new, changed, or all" >&2
    exit 2
    ;;
esac

if [ "$REQUIRE_EVALS" = "true" ]; then
  args+=(--require-evals)
fi

skills_file="$(mktemp)"
trap 'rm -f "$skills_file"' EXIT
python3 scripts/list-skills-for-assurance.py "${args[@]}" > "$skills_file"

if [ ! -s "$skills_file" ]; then
  echo "No skills selected for eval checks (scope=$MODE)."
  exit 0
fi

if [ "$MODE" = "all" ]; then
  echo "::group::Tessl eval check: all skills"
  tessl eval lint . | tee ".tessl/eval-results/all-skills-lint.txt"
  if [ "$RUN_EVALS" = "true" ]; then
    tessl eval run . \
      --label "${LABEL_PREFIX}-all-skills-${GITHUB_RUN_ID:-local}" \
      --yes \
      --json \
      | tee ".tessl/eval-results/all-skills-run.json"
  else
    echo "RUN_EVALS=false; skipped remote Tessl eval run for all skills."
  fi
  echo "::endgroup::"
  exit 0
fi

while IFS= read -r skill; do
  [ -n "$skill" ] || continue
  echo "::group::Tessl eval check: $skill"
  echo "Linting eval scenario corpus before evaluating $skill"
  tessl eval lint . | tee ".tessl/eval-results/${skill}-lint.txt"
  if [ "$RUN_EVALS" = "true" ]; then
    tessl eval run . \
      --skill "$skill" \
      --label "${LABEL_PREFIX}-${skill}-${GITHUB_RUN_ID:-local}" \
      --yes \
      --json \
      | tee ".tessl/eval-results/${skill}-run.json"
  else
    echo "RUN_EVALS=false; skipped remote Tessl eval run for $skill."
  fi
  echo "::endgroup::"
done < "$skills_file"

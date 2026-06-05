#!/usr/bin/env bash
# preflight.sh — deterministic environment + inventory report for /harness-init.
# Prints a checklist; does NOT gate. The skill reads this and decides what to do.
# Run from the consumer project's root (the human's checkout).

ok()   { printf '  [ok]   %s\n' "$1"; }
warn() { printf '  [warn] %s\n' "$1"; }
miss() { printf '  [MISS] %s\n' "$1"; }
have() { command -v "$1" >/dev/null 2>&1; }

echo "=== Environment ==="
if git rev-parse --git-dir >/dev/null 2>&1; then
  ok "git repository"
  branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "?")
  [[ "$branch" == "main" || "$branch" == "master" ]] && ok "on $branch" || warn "on '$branch' (expected main)"
  git diff --quiet && git diff --cached --quiet 2>/dev/null && ok "working tree clean" || warn "working tree has uncommitted changes"
  git remote get-url origin >/dev/null 2>&1 && ok "origin remote: $(git remote get-url origin 2>/dev/null)" || warn "no 'origin' remote (needed for branch-as-queue)"
  echo "  git email: $(git config user.email 2>/dev/null || echo '(unset!)')"
  echo "  derived slug: $(git config user.email 2>/dev/null | cut -d@ -f1)"
else
  miss "not a git repository — run 'git init' and add an origin remote first"
fi
have git    && ok "git CLI"    || miss "git CLI"
have gh      && { gh auth status >/dev/null 2>&1 && ok "gh CLI (authenticated)" || warn "gh CLI present but not authenticated (run: gh auth login)"; } || miss "gh CLI (needed for PR ops)"
have claude  && ok "claude CLI" || warn "claude CLI not on PATH (the dispatcher shells out to 'claude -p')"

echo
echo "=== Toolchain signals (for AGENTS.md / local-checks / bootstrap) ==="
declare -A M=(
  [package.json]="Node" [pnpm-lock.yaml]="pnpm" [yarn.lock]="yarn" [bun.lockb]="bun"
  [pyproject.toml]="Python" [requirements.txt]="pip" [uv.lock]="uv" [Pipfile]="pipenv"
  [Cargo.toml]="Rust" [go.mod]="Go" [Gemfile]="Ruby" [pom.xml]="Maven"
  [build.gradle]="Gradle" [composer.json]="PHP" [mix.exs]="Elixir"
)
found=0
for f in "${!M[@]}"; do [[ -e "$f" ]] && { ok "${M[$f]} ($f)"; found=1; }; done
(( found )) || warn "no dependency manifest found at root — discovery will rely on README/CI or asking"
for f in .env.example .env.sample .env.template; do [[ -e "$f" ]] && warn "secrets template: $f (bootstrap will need to copy the real file)"; done
[[ -e Makefile || -e Justfile || -e Taskfile.yml ]] && ok "task runner present (read it for canonical commands)"
[[ -d .github/workflows ]] && ok ".github/workflows present (read CI for setup+test recipe)"
[[ -e prisma/schema.prisma ]] && warn "prisma — bootstrap likely needs 'prisma generate'"
ls ./*.proto >/dev/null 2>&1 && warn "protobuf — bootstrap likely needs a codegen step"

echo
echo "=== Inner skills (chain the dispatcher calls) ==="
SK=.claude/skills
for s in intent spec-planning spec-validate implement-mainspec fix-local-checks address-feedback learn expert; do
  if find "$SK" -type f -path "*/$s/SKILL.md" 2>/dev/null | grep -q . ; then ok "/$s"
  elif find "$SK" -type d -name "$s" 2>/dev/null | grep -q . ; then warn "/$s (dir present but no SKILL.md — stub?)"
  else miss "/$s (not installed)"; fi
done

echo
echo "=== Harness artifacts (re-run / already-present check) ==="
[[ -f scripts/poll-and-dispatch.sh ]] && warn "scripts/poll-and-dispatch.sh exists (re-run?)" || ok "scripts/poll-and-dispatch.sh absent (fresh)"
[[ -f scripts/harness-tick.sh ]] && warn "scripts/harness-tick.sh exists (re-run?)" || ok "scripts/harness-tick.sh absent (fresh)"
[[ -f scripts/harness-lib.sh ]] && warn "scripts/harness-lib.sh exists (re-run?)" || ok "scripts/harness-lib.sh absent (fresh)"
[[ -f scripts/learn-tick.sh ]] && warn "scripts/learn-tick.sh exists (re-run?)" || ok "scripts/learn-tick.sh absent (fresh)"
[[ -f .harness/env ]] && warn ".harness/env exists (re-run?)" || ok ".harness/env absent (fresh)"
[[ -s AGENTS.md ]] && warn "AGENTS.md is non-empty (re-run? will diff)" || ok "AGENTS.md absent/empty (fresh)"
[[ -f scripts/bootstrap-worktree.sh ]] && warn "scripts/bootstrap-worktree.sh exists (re-run?)" || ok "scripts/bootstrap-worktree.sh absent (fresh)"
[[ -f REVIEW.md ]] && warn "REVIEW.md exists" || ok "REVIEW.md absent"
# Preflight runs from the HUMAN's checkout (bare repo name), so basename "$PWD" is
# the right base for the expected host-worktree path here. (The dispatcher, which
# runs from the host worktree, instead derives this from the main worktree.)
base="../$(basename "$PWD")-harness"
[[ -d "$base" ]] && warn "host worktree $base already exists" || ok "host worktree $base absent (fresh)"

echo
echo "Preflight complete. [MISS] items block; [warn] items need a decision."

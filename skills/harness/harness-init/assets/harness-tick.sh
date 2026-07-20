#!/usr/bin/env bash
# harness-tick.sh — one outer-loop tick: sync the HOST worktree to main, then dispatch.
#
# This is the target the build loop (/loop, cron, …) invokes — NOT the dispatcher
# directly. It exists to keep the harness's own operating context current.
#
# WHY A WRAPPER. The dispatcher, scripts/bootstrap-worktree.sh, and .harness/env all
# live in the HOST worktree (../<repo>-harness) and are read FROM it as the loop runs.
# The host worktree sits at a detached HEAD and does NOT auto-advance when main moves,
# so without a sync step those would freeze at whatever commit the worktree was created
# on. Feature PIPELINE skills are unaffected — they run inside per-feature worktrees
# that branch from the PRD branch (off main), so new features pick up skill updates on
# their own. Only this loop-level infrastructure needs syncing; that's what this
# wrapper does. (The /learn skill + memory used to need this sync too, back when /learn
# ran in the host worktree; it now runs in its own dedicated worktree under its own
# loop — scripts/learn-tick.sh — which syncs itself, so the host worktree is purely the
# build loop's.)
#
# WHY HERE AND NOT IN THE DISPATCHER. The dispatcher must stay HEAD-agnostic: if it
# reset its own checkout mid-run it would overwrite the very file it's executing
# (and its flock is on $0). Doing the sync HERE, before exec, means the dispatcher
# always loads its freshest version cleanly. This wrapper is tiny and stable; on the
# rare occasion it changes on main, that change simply takes effect the next tick.

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."   # repo root of the host worktree

git fetch --quiet origin

# Force a clean, current detached checkout of origin/main. `-f --detach` is
# idempotent and self-healing: it recovers no matter what state a crash left the
# worktree in. This is the host-worktree analogue of the dispatcher's per-feature
# wipe. The memory loop never touches this worktree's working tree (it works in
# ../<repo>-harness-learn), so there is nothing here to race.
git checkout --quiet -f --detach origin/main
git clean -qfd                            # -d not -x: keep node_modules & .harness/* runtime state

exec ./scripts/poll-and-dispatch.sh "$@"

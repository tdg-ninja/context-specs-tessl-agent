---
name: poll-and-dispatch
description: One tick of the harness outer loop. Syncs the host worktree to main, then dispatches one skill per branch. Run on an interval via /loop.
---

# poll-and-dispatch

Run `./scripts/harness-tick.sh` from the harness host worktree root and report what it did.

That is the entire skill. The intelligence is in the scripts — this exists only
so `/loop` has a slash-command-shaped target. Do not do any feature work in this
session; the scripts shell out to fresh `claude -p` subprocesses for all real
work, which is what keeps this outer session's context from bloating across ticks.

`harness-tick.sh` first force-syncs this host worktree to a clean `origin/main`
(so the dispatcher, `.harness/env`, the `/learn` skill, memory, and `AGENTS.md`
are always current), then `exec`s `./scripts/poll-and-dispatch.sh` — the
deterministic, HEAD-agnostic dispatcher. Never point `/loop` at the dispatcher
directly, or loop-infrastructure updates merged to main won't reach the loop.

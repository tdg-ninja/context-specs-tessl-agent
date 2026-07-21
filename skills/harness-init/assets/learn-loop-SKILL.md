---
name: learn-loop
description: One tick of the harness MEMORY loop. Checks whether main advanced since the last memory update and, if so, runs /learn in a dedicated worktree to open a learn/<sha> PR. Run on an interval via /loop, alongside the build loop.
---

# learn-loop

Run `./scripts/learn-tick.sh` from the harness host worktree root and report what it did.

That is the entire skill. The intelligence is in the script — this exists only so
`/loop` has a slash-command-shaped target. Do not do any memory work in this session;
the script shells out to a fresh `claude -p "/learn …"` subprocess for the real work,
in its own `../<repo>-harness-learn` worktree, which is what keeps this outer session's
context from bloating across ticks.

`learn-tick.sh` is the memory-loop counterpart of `harness-tick.sh`. It self-serializes
with its own `flock` (independent of the build loop), syncs a dedicated, reused learn
worktree to a clean `origin/main`, and — unless a `learn/<sha>` PR is already open
(it pauses while one awaits your review) — computes the range from the
`refs/harness/last-learned` watermark to current main and runs `/learn` over it. It
never touches the build loop's host worktree, so the two loops run fully in parallel.

Start it alongside the build loop, from the same harness host worktree:

```
/loop 10m /learn-loop
```

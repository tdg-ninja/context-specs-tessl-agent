# Mental model — what the harness is

Read this first. It is the condensed version of the design doc, written so the
skill can explain the harness to a developer who has never seen it. When you
walk a user through setup, narrate from this — do not assume they have read the
design doc.

## One sentence

The harness is a polling loop that watches a git branch namespace, and for each
feature in flight, runs exactly one spec-driven-development step per tick in an
isolated worktree, until a PR is open against `main` for a human to merge.

## Three layers, independent

```
OUTER LOOP        a long-lived Claude Code session (/loop 5m), or cron, or CI.
  |               Owns TIMING only. Knows nothing about the work.
  v
TICK WRAPPER      scripts/harness-tick.sh. Syncs the host worktree to a clean
  |               origin/main, then execs the dispatcher. Keeps loop infra fresh.
  v
DISPATCHER        scripts/poll-and-dispatch.sh. Pure bash, zero LLM calls.
  |               Owns ROUTING: reads disk, decides the next skill per branch,
  v               shells out. The if/elif chain IS the state machine.
INNER LOOP        one fresh `claude -p "/skill ..."` subprocess per step.
                  Owns THE WORK. Fresh context every time, exits when done.
```

You can swap any layer without touching the others. harness-init sets up the
outer loop, the tick wrapper, and the dispatcher; the inner skills come from the
catalog.

This stack is the **build loop** (features). There is a second, independent loop
with the same shape — the **memory loop**: `/loop … /learn-loop` →
`scripts/learn-tick.sh` → one `claude -p "/learn …"` in the dedicated
`<repo>-harness-learn` worktree. It runs post-merge memory updates without ever
blocking (or being blocked by) the build loop; the two coordinate only through git
(the `refs/harness/last-learned` watermark ref). Same three-layer discipline, its own
`/loop` session.

## Three checkouts (the worktree topology)

```
<repo>/                       the human's checkout. On `main`. Never touched by the harness. (Inv 6)
<repo>-harness/               the harness HOST worktree. Detached at origin/main; runs BOTH loops'
                              outer sessions. harness-tick.sh re-syncs it to main every tick. Does
                              NOT move between feature branches.
<repo>-harness-<feature>/     EPHEMERAL per-feature worktree. One per in-flight feature; the
                              dispatcher creates it (off feature/<feature>) and tears it down on
                              merge/close. (Inv 3: worktree ↔ branch 1:1.)
<repo>-harness-learn/         the memory loop's dedicated worktree. Persistent + reused; learn-tick.sh
                              resets it to a clean learn/<sha> off main each run. Where /learn runs.
```

Two reasons the host is **detached**, not on a `main` branch: git refuses to check
out `main` in two worktrees at once (the human's checkout holds it), and the host
never needs a writable branch of its own — it only reads loop infra and spawns
per-feature worktrees. `WORKTREE_BASE` derives `<repo>` from the **main worktree**
(not `$PWD`), so per-feature paths are always `<repo>-harness-<feature>` no matter
which worktree the dispatcher runs from.

## Why the split matters for setup

- **The outer loop must never do real work.** `/loop 5m /poll-and-dispatch`
  re-runs in the *same* session every tick; if it did work there, context would
  bloat and rot by tick 10. The shim skill does one thing: call the script. All
  real work happens in `claude -p` subprocesses with fresh context.
- **The dispatcher is deterministic.** No model in the decision path. This is
  what makes crash recovery free and behavior predictable from disk state.

## The state machine in one table

| Branch state           | Means              | Next action the dispatcher takes        |
|------------------------|--------------------|-----------------------------------------|
| `prd/<author>/<f>`     | waiting in queue   | atomic-rename to `feature/<f>` (claim)  |
| `feature/<f>` no specs | claimed, unplanned | `/spec-planning`                        |
| `.planning-done`       | planned            | `/spec-validate`                        |
| `.validated`           | validated          | `/implement-mainspec` until runner == 0 |
| runner exits 0         | implemented        | open PR against `main`                  |
| PR has findings        | in review          | `/address-feedback` (bounded)           |
| PR merged              | done               | cleanup worktree (the memory loop runs `/learn` separately) |

"Done" is one thing only: `./prds/<f>/run-prd-test.sh` exits 0. The harness
contracts on that exit code and nothing else.

## The artifacts ARE the state

There is no database, no in-memory queue, no "what step are we on" file. A
sentinel file existing IS that phase being done. The branch namespace IS the
work registry. Counters live in `.harness/`. Everything the dispatcher needs is
re-derivable from `git` + the filesystem on every tick. That is the whole
recovery story: `kill -9` mid-step leaves nothing the next tick can't sort out.

## Where the human steers

Exactly two points:
1. **Confirming a PRD** (via `/intent`, in their own checkout).
2. **Merging a PR** (the feature PR, and later the `/learn` memory PR).

Everything between is the harness. The loop never merges — that is the steering
input the system is built around.

## What harness-init is actually standing up

Both outer loops (two `/loop` sessions — build + memory), the dispatcher and
`learn-tick.sh` scripts plus their shared `harness-lib.sh`, the config, the
agent contract (`AGENTS.md`), and the provisioning that makes per-feature
worktrees runnable. The inner skills (`/intent`, `/spec-planning`, etc.) are
installed from the catalog; harness-init wires them, it does not author them.

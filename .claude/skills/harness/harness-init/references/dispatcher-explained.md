# The dispatcher, explained

When you drop `assets/poll-and-dispatch.sh` into the project, walk the user
through it using this file. The goal: the user understands every section well
enough to decide whether to tweak it. Never present it as a black box.

## What it is

`scripts/poll-and-dispatch.sh` — ~150 lines of bash, `git`, and `gh`. No LLM in
the decision path. It runs once per tick. The `if/elif` chain is the state
machine; the artifacts on disk are the state.

## The six load-bearing properties

Explain these as the "why it's safe" of the script. Each maps to an invariant.

1. **One transition per tick per branch.** The `if/elif` fires at most one
   branch. Next tick, the artifact this tick wrote satisfies the condition and
   the *next* `elif` fires. Forward, one step at a time. (Inv 5)
2. **Artifacts are the only state.** A sentinel existing IS that phase being
   done. No checkpoint file. Crash recovery is free — next tick re-derives from
   disk. (Inv 1 + 4) Most sentinels are written by the skills; `specs/<f>/.prd-passed`
   is the exception — the *dispatcher* commits+pushes it the first time
   `run-prd-test.sh` exits 0, so a runner that shells out to an LLM-as-judge runs
   once instead of every tick (and can't non-deterministically re-kick implement).
3. **Wipe + HEAD-check before every advance.** `git reset --hard && git clean
   -fd` discards a crashed skill's uncommitted mess; the HEAD guard skips any
   worktree whose branch doesn't match the feature being advanced, so a
   manually-checked-out branch is never clobbered. Runs only in per-feature
   worktrees. (Inv 3 + 6)
4. **Dispatcher never invokes an LLM directly.** It only spawns `claude -p`
   subprocesses or shells to `git`/`gh`. Each subprocess is a fresh process and
   a clean context window. (Inv 5)
5. **Local checks are optional and bounded.** If `scripts/local-checks.sh`
   exists, the PR is gated on it with a two-strike retry (auto-fix, then focused
   LLM fix, then stop). No script = gate skipped. (Inv 8)
6. **`MAX_WORKTREES` is the one concurrency knob.** Default 1 = FIFO single
   worktree. Claims are lazy: PRDs over capacity stay in `prd/<slug>/*` as the
   visible queue. In-flight work always continues regardless of cap changes.
   (Inv 2 + 3)

## Section-by-section map

| Lines (approx) | Section | Tweakable? |
|----------------|---------|------------|
| top | `flock -n` self-lock | No — serializes ticks; load-bearing. |
| config block | `SLUG`, `WATCH`, `WORKTREE_BASE`, `MAX_WORKTREES` | Via `.harness/env`, not by editing here. `WORKTREE_BASE` derives `<repo>` from the **main worktree**, not `$PWD` — so per-feature paths are `<repo>-harness-<feature>` even though the dispatcher runs from the `<repo>-harness` host worktree. |
| `has_prd()` | Invariant-2 ownership filter | No — defines what "harness-owned" means. |
| step 1 | re-attach in-flight worktrees | The `bootstrap_worktree` hook call is the local addition (see below). |
| step 2 | lazy claim up to capacity | No — atomic rename is the claim lock. |
| step 3 | advance each feature one step | **This is where you add/remove pipeline steps** — one `elif` per step. |
| step 4 | cleanup merged/closed PRs | Safe to extend (e.g., notify on cleanup). |
| step 5 | post-merge `/learn` (memory update, ground truth only) | Debounce/idempotency live here. |
| helpers | `run_claude` (session-tagged invocation + TSV log) and `signal_stuck` (PR-body STUCK signal) | Used by every step in §3 that calls `claude -p` or hits a cap. |

## The bootstrap hook — project-owned worktree provisioning

A bare worktree has no `node_modules`, no `.env`, no generated code — so slice
signals and the PRD runner fail for reasons unrelated to the feature. So
immediately after every `git worktree add`, the dispatcher runs
`scripts/bootstrap-worktree.sh "$wt"` if that script exists and is executable.
The hook itself is canonical (the design doc's dispatcher includes it); what's
**project-owned** is the `bootstrap-worktree.sh` it calls — harness-init generates
that per project (see `worktree-bootstrap.md`). If the project has no bootstrap
script, the hook is a no-op.

Make sure the user knows: this hook is why the per-feature worktrees the harness
spins up are actually runnable.

## The tick wrapper — keeping the host worktree current (`harness-tick.sh`)

The dispatcher is **HEAD-agnostic**: it operates on git *refs* (`origin/feature/*`,
`feature/*`) and per-feature worktrees, never on its own checkout's HEAD. But the
files it executes — the dispatcher itself, `bootstrap-worktree.sh`, `.harness/env`,
and (for step 5) the `/learn` skill + memory + root `AGENTS.md` — are read from the
**host worktree**, which sits at a detached HEAD and does not auto-advance when
`main` moves. Without a sync step, loop infrastructure freezes at the commit the
host worktree was created on.

So the outer loop targets **`scripts/harness-tick.sh`**, not the dispatcher
directly. The wrapper:

1. `git fetch origin`
2. `git checkout -f --detach origin/main` + `git clean -fd` — force the host worktree
   to a clean, current `main` (idempotent; self-heals whatever state a crash or a
   prior `/learn` left it in)
3. `exec ./scripts/poll-and-dispatch.sh`

The sync lives in the wrapper, **before** `exec`, for a reason: if the dispatcher
reset its own checkout mid-run it would overwrite the very file it's executing (and
its `flock` is on `$0`). Doing it in the wrapper means the dispatcher always loads
its freshest version cleanly. The wrapper is tiny and stable; on the rare tick where
it changes on main, that change takes effect the next tick.

Note the asymmetry: feature **pipeline** skills (`/spec-planning`, `/implement-*`,
`/address-feedback`, …) do **not** need this sync — they run inside per-feature
worktrees that branch from the PRD branch (off main), so new features pick up skill
updates on their own. Only loop-level infra and `/learn`-time context ride the host
worktree, and that's exactly what the wrapper refreshes. The `/learn` step keeping
cwd `"."` (the host worktree) is therefore safe — the wrapper guarantees `"."` is a
clean checkout of main each tick, so no dedicated `/learn` worktree is needed.

## Memory is single-path; STUCK is the third human-steering point

Memory has **one write path** — `/learn` at step 5, post-merge, ground truth only.
There is no separate write path for failed features. Instead, **STUCK** (a step in
§3 hitting its cap) is treated as a first-class escalation: the dispatcher posts
to the PR (opening it as a draft if needed) with the session log, the failing
output tail, and a diagnosis-first checklist, then halts the feature. The
human's first job at STUCK is to identify the **context defect** (which
`AGENTS.md` / Expert / spec / PRD content misled the agent), correct it on the
branch, *then* fix the code, *then* merge. Those context corrections ride into
main with the merge, where `/learn` picks them up and routes any follow-ups.

This is why the design no longer has any "Path B" / `lessons.md` machinery —
the human's hands-on diagnosis + correction at STUCK is the learning, and the
merge carries it home.

## The session log + STUCK signal

Two small helpers, both above step 1, do the legwork:

- **`run_claude <step> <feature> <attempt#> <wt> "<skill cmd>"`** — wraps every
  `claude -p` call. `cd`s into the worktree `<wt>` first (there is no print-mode
  `--cwd` flag, and the `cd` is what gives the skill its `.claude/` command +
  `AGENTS.md` discovery; `learn` passes `.` to run at the repo root on `main`).
  Generates a UUID session id, runs `claude -p --session-id "${CLAUDE_PERM_ARGS[@]}"`,
  and appends `<timestamp>\t<step>\t<attempt>\t<session_id>\t<exit>\t<duration>`
  to `.harness/sessions-<feature>.tsv` (gitignored, cleared on merge/close). A
  non-zero skill exit is recorded in the row but never aborts the tick (`return 0`).
- **`signal_stuck <feature> <step> <cap> [output-file]`** — touches the stuck
  sentinel, composes a PR body (step, cap, tail of the session log, optional tail
  of the failing output, diagnosis-first checklist), and either opens a draft PR
  or comments on an existing one. This is the single human-facing surface.

If your `claude -p` version doesn't support `--session-id`, swap that flag for
`--output-format json` and parse `session_id` from stdout — `run_claude` is the
one place to change.

## Common tweaks to offer

- **Add a pipeline step** (e.g. `/security-review` between validate and
  implement): insert one `elif` in step 3 with its own sentinel check, its own
  `<step>_CAP`, and a `run_claude` / `signal_stuck` pair like the others.
- **STUCK caps** (all built in): `PLANNING_CAP`, `VALIDATE_CAP`, `IMPLEMENT_CAP`,
  `LOCAL_CHECKS_CAP`, `FEEDBACK_CAP`. All env-overridable in `.harness/env`.
  Raise for hard features, lower to fail fast.
- **Debounce window** for `/learn`: currently fires whenever `origin/main` sha
  changed. A team merging many times per minute may want a time-debounce.

## What NOT to let the user do

- Add `&` to any `claude -p` call (breaks synchronous one-step discipline).
- Add an LLM call to the decision logic (breaks Inv 5, makes it non-reproducible
  and a cost surface).
- Remove the wipe or the HEAD guard (breaks crash recovery and Inv 6).
- Replace the atomic-rename claim with a marker file (breaks Inv 2 + 7).
- Point `/loop` at `poll-and-dispatch.sh` directly, bypassing `harness-tick.sh`
  (loop-infra updates merged to main would never reach the running loop).
- Move the host-worktree sync *into* the dispatcher (it would overwrite its own
  running file; the sync belongs in the wrapper, before `exec`).

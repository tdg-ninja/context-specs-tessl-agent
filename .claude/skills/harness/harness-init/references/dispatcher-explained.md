# The dispatcher, explained

When you drop `assets/poll-and-dispatch.sh` into the project, walk the user
through it using this file. The goal: the user understands every section well
enough to decide whether to tweak it. Never present it as a black box.

## What it is

`scripts/poll-and-dispatch.sh` — ~150 lines of bash, `git`, and `gh`. No LLM in
the decision path. It runs once per tick. The `if/elif` chain is the state
machine; the artifacts on disk are the state.

## The seven load-bearing properties

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
7. **Convergence has its own exit — HUMAN_REVIEW — separate from STUCK.** The
   review loop's healthy end is the reviewer posting `REVIEW_CLEAN_MARKER`;
   `reviewer_converged` sees it and writes `human-review-<f>`, the guard posts the
   session trail once and halts the feature for the human's `/evaluate-pr`. The
   marker (not sticky review state) is the signal, so a clean PR can't false-STUCK
   on a stale `COMMENTED` review. If the reviewer never marks clean, the feedback
   cap STUCKs instead — fine, the human merges.

## Section-by-section map

| Lines (approx) | Section | Tweakable? |
|----------------|---------|------------|
| top | `flock -n` self-lock | No — serializes ticks; load-bearing. |
| config block | `SLUG`, `WATCH`, `WORKTREE_BASE`, `MAX_WORKTREES` | Via `.harness/env`, not by editing here. `WORKTREE_BASE` derives `<repo>` from the **main worktree**, not `$PWD` — so per-feature paths are `<repo>-harness-<feature>` even though the dispatcher runs from the `<repo>-harness` host worktree. |
| `has_prd()` | Invariant-2 ownership filter | No — defines what "harness-owned" means. |
| step 1 | re-attach in-flight worktrees | The `bootstrap_worktree` hook call is the local addition (see below). The PR-state **liveness gate** (skip `MERGED`/`CLOSED` features) is load-bearing — don't drop it; see "Liveness" below. |
| step 2 | lazy claim up to capacity | No — atomic rename is the claim lock. |
| step 3 | advance each feature one step | **This is where you add/remove pipeline steps** — one `elif` per step. |
| step 4 | cleanup merged/closed PRs | Safe to extend (e.g., notify on cleanup). |
| post-merge `/learn` | **NOT in this script** — runs in the separate memory loop (`learn-tick.sh`). See "The memory loop" below. | Watermark/idempotency live there. |
| step 3 (review) | the feedback gate has three branches: `reviewer_converged` (marker present) → write `human-review-<f>`; else findings → `/address-feedback`; else cap → STUCK | Convergence is the marker; the gate order matters (converge before the findings loop). |
| helpers (shared) | `run_claude` (session-tagged invocation + TSV log), `render_sessions_table` (shared trail renderer) live in `harness-lib.sh` — both loops use them. | Edit `run_claude` in one place (e.g. the `--session-id` swap). |
| helpers (dispatcher) | `signal_stuck` (PR-body STUCK signal), `signal_human_review` (the convergence handoff comment), `reviewer_converged` (marker check), `has_prd` (ownership filter) | Used by §3 steps that call `claude -p`, hit a cap, or detect convergence. |

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

## Liveness — branch existence is not in-flight (the step-1 PR-state gate)

`has_prd()` answers *ownership* ("is this a harness feature?"), not *liveness*
("is there still work to do?"). A `feature/<f>` whose PR has **merged** keeps both
its branch (GitHub's delete-on-merge is off by default, and you can't make every
consumer enable it) and its committed PRD — so `has_prd()` stays true forever.
Without a liveness check, step 1 re-attaches that finished feature as in-flight on
*every* tick, which does two bad things at once:

1. step 3 re-fires `/address-feedback` on the merged PR — wasted tokens, every tick;
2. the phantom occupies a `MAX_WORKTREES` slot, so `capacity` (step 2) drops and a
   freshly-filed PRD sits unclaimed in the queue behind a feature that's already done.

Step 4 cleanup notices the merge and removes the *local* worktree, but it runs
*after* step 3 and doesn't delete the *remote* branch — so the next tick's step 1
re-attaches the same ghost. The fix is one gate in step 1, right after `has_prd`:
`gh pr view` the feature's PR and `continue` past any `MERGED`/`CLOSED` one. Because
the in-flight set is what feeds the capacity math, that single skip cures both
symptoms. Notes:

- **No branch deletion.** We never `git push --delete` a merged feature branch —
  the harness simply stops treating it as live work. Consumers keep whatever
  branch-retention policy they like.
- **Fail-safe on empty state.** A feature still in a pre-PR phase
  (planning/validate/implement) has no PR, and a transient `gh` outage also returns
  empty — both are kept in-flight so live work is never silently dropped.
- **Forward-only (Inv 9).** Merged is terminal; the gate only ever skips, never rewinds.

## The tick wrapper — keeping the host worktree current (`harness-tick.sh`)

The dispatcher is **HEAD-agnostic**: it operates on git *refs* (`origin/feature/*`,
`feature/*`) and per-feature worktrees, never on its own checkout's HEAD. But the
files it executes — the dispatcher itself, `harness-lib.sh`, `bootstrap-worktree.sh`,
`.harness/env` — are read from the **host worktree**, which sits at a detached HEAD
and does not auto-advance when `main` moves. Without a sync step, loop infrastructure
freezes at the commit the host worktree was created on.

So the build loop targets **`scripts/harness-tick.sh`**, not the dispatcher
directly. The wrapper:

1. `git fetch origin`
2. `git checkout -f --detach origin/main` + `git clean -fd` — force the host worktree
   to a clean, current `main` (idempotent; self-heals whatever state a crash left it in)
3. `exec ./scripts/poll-and-dispatch.sh`

The sync lives in the wrapper, **before** `exec`, for a reason: if the dispatcher
reset its own checkout mid-run it would overwrite the very file it's executing (and
its `flock` is on `$0`). Doing it in the wrapper means the dispatcher always loads
its freshest version cleanly. The wrapper is tiny and stable; on the rare tick where
it changes on main, that change takes effect the next tick.

Note the asymmetry: feature **pipeline** skills (`/spec-planning`, `/implement-*`,
`/address-feedback`, …) do **not** need this sync — they run inside per-feature
worktrees that branch from the PRD branch (off main), so new features pick up skill
updates on their own. Only loop-level infra rides the host worktree, and that's
exactly what the wrapper refreshes.

## The memory loop — `/learn` as its own loop (`learn-tick.sh`)

`/learn` is **not** a dispatcher step. It runs in a second, independent loop:
`/loop … /learn-loop` → `scripts/learn-tick.sh`. This is the deliberate decoupling
that keeps a multi-minute Expert bootstrap from blocking (or being blocked by) the
build loop. The two loops share a node but never wait on each other — separate
`flock`s on separate scripts — and coordinate only through git (Inv 1 + 7).

What `learn-tick.sh` does each tick (it is the memory-loop analogue of
`harness-tick.sh` + the old dispatcher step 5):

1. `flock -n` on itself (self-serialize — a long bootstrap just no-ops later ticks).
2. `git fetch` `main` **and** the watermark ref namespace
   (`+refs/harness/*:refs/harness/*`). Fetch only — never the host *working tree*.
3. Ensure the dedicated, **reused** `../<repo>-harness-learn` worktree exists (create
   + `bootstrap_worktree` on first run — so a drafted lint and `check-agents-md.sh`
   can actually run), then reset it to clean `origin/main` (`-fd`, keeping deps).
4. **Pause** if a `learn/<sha>` PR is already open (`gh pr list … startswith("learn/")`):
   memory edits serialize behind human review. Nothing is queued — the backlog is
   implicit in `(watermark, origin/main)` and recomputed every tick.
5. Compute `since = refs/harness/last-learned` (or a bounded look-back on the first
   run), `to = origin/main`; if equal, no-op.
6. `git ls-remote origin learn/<to>` idempotency (cross-node first-to-push-wins).
7. Check out `learn/<to>` in the learn worktree and run `/learn --since <since>
   --sha <to>` there. `/learn` writes memory, pushes the branch, opens the PR.
8. `signal_learn_review` posts the session trail on the PR (if one opened).
9. Advance `refs/harness/last-learned` to `<to>` with an atomic CAS
   (`--force-with-lease`) — the same first-to-push-wins primitive used to claim PRDs.

**Why a ref watermark, not the old `.harness/last-main-sha` file.** A ref lives in
its own namespace nothing cleans, so it survives `learn/<sha>` branch deletion; it's
on the remote, so it's shared across nodes; and `--force-with-lease` gives a
lock-free compare-and-swap. The file was per-node local state with none of those
properties. The advance happens whether or not `/learn` opened a PR (a 0/3 no-op
merge is still "learned"), matching the old step-5 semantics — only now the anchor is
durable and shared.

**Why this never races the build loop.** `learn-tick.sh` does all working-tree ops
(`checkout`/`reset`/`clean`) in the `-harness-learn` worktree, never the host
worktree — so the build loop's per-tick host force-sync has nothing of the memory
loop's to wipe. That is what let us delete the old `.harness/learn-running` PID guard
entirely: there is no longer a skill running *in* the host worktree to protect.

## Human-steering points: Evaluate (HUMAN_REVIEW) and STUCK

The human steers the machine at three touchpoints (the Human Loop — confirm a PRD,
evaluate-then-merge a PR, unstick a STUCK). Two of those live in this script.

**HUMAN_REVIEW (the healthy one).** When the reviewer converges (posts
`REVIEW_CLEAN_MARKER`), `reviewer_converged` writes `human-review-<f>`; the guard
posts the build-session trail once and halts the feature. The human runs
`/evaluate-pr` to walk the change, run it, and merge (or fix-and-push, or close).
The loop does not re-engage — the human is the last mile.

**STUCK (the failure one).** Memory still has **one write path** — `/learn` in the
memory loop, post-merge, ground truth only. There is no separate write path for failed features.
Instead, **STUCK** (a step in §3 hitting its cap) is a first-class escalation: the
dispatcher posts
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

A few small helpers do the legwork. `run_claude` and `render_sessions_table` are
**shared** — they live in `harness-lib.sh`, sourced by both the dispatcher and
`learn-tick.sh`; the rest are dispatcher-local, defined above step 1:

- **`run_claude <step> <feature> <attempt#> <wt> "<skill cmd>"`** (shared) — wraps every
  `claude -p` call. `cd`s into the worktree `<wt>` first (there is no print-mode
  `--cwd` flag, and the `cd` is what gives the skill its `.claude/` command +
  `AGENTS.md` discovery; the build loop passes the per-feature worktree, the memory
  loop passes the `<repo>-harness-learn` worktree).
  Generates a UUID session id, runs `claude -p --session-id "${CLAUDE_PERM_ARGS[@]}"`,
  and appends `<timestamp>\t<step>\t<attempt>\t<session_id>\t<exit>\t<duration>`
  to `.harness/sessions-<feature>.tsv` (gitignored, cleared on merge/close). A
  non-zero skill exit is recorded in the row but never aborts the tick (`return 0`).
- **`signal_stuck <feature> <step> <cap> [output-file]`** — touches the stuck
  sentinel, composes a PR body (step, cap, tail of the session log, optional tail
  of the failing output, diagnosis-first checklist), and either opens a draft PR
  or comments on an existing one. The single human-facing surface for failures.
- **`reviewer_converged <branch>`** — true iff a PR comment contains
  `REVIEW_CLEAN_MARKER`. One `gh` call, no LLM; deliberately no freshness/author
  check (see the helper's comment). Empty marker = no reviewer → false.
- **`signal_human_review <feature>`** — the convergence counterpart of
  `signal_stuck`: posts the "Ready for your review" comment with the session trail
  (via the shared `render_sessions_table`) so the human can `/evaluate-pr`.
- **`signal_learn_review <feature> <branch>`** — lives in **`learn-tick.sh`**, not the
  dispatcher: after `/learn` opens its `learn/<sha>` PR, posts the headless session
  trail (via the shared `render_sessions_table`) framed for troubleshooting *why*
  `/learn` routed each fact as it did, so the human evaluating the memory PR can open
  the trace before accepting or revising it. Uses a per-sha session label
  (`learn-<sha>`) so the table shows exactly that run.

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
- **Memory-loop cadence** for `/learn`: it lives in `learn-tick.sh`, not here. It
  fires whenever `origin/main` advanced past the `refs/harness/last-learned` watermark
  and no `learn/<sha>` PR is open. A team merging many times per minute can simply run
  `/loop` at a longer interval — each run batches every merge since the watermark.

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
- Point the memory loop's `/loop` at `poll-and-dispatch.sh`, or fold `/learn` back
  into the dispatcher as a step — that re-couples the loops, so a multi-minute Expert
  bootstrap again blocks every feature step (the whole reason it's a separate loop).
- Make `learn-tick.sh` do working-tree ops (`checkout`/`reset`/`clean`) in the **host**
  worktree instead of `<repo>-harness-learn` — it would then race the build loop's
  per-tick host force-sync. The memory loop must stay in its own worktree.

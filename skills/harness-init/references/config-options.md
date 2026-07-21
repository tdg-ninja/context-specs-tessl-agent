# Config options — `.harness/env`

The harness has a small, deliberately tiny config surface. All of it lives in
`.harness/env` (sourced by the dispatcher) or in the `/loop` invocation. When
you walk the user through config, explain each knob's tradeoff and recommend the
default; only change a default if the user has a concrete reason.

## The knobs

### `MAX_WORKTREES` (default `1`)

How many features the harness works in parallel.

- **`1` (recommended default).** Single worktree, FIFO. One feature at a time.
  No disk multiplication, no duplicate `node_modules`/`target`, simplest mental
  model. Right for essentially every single-developer project.
- **`2`+.** Bounded parallelism. Each concurrent feature gets its own worktree
  (`${WORKTREE_BASE}-${feature}`), so disk and rebuild cost multiply. Flip this
  only when you have several independent features queued AND surplus disk/CI.

In-flight work always continues regardless of this value — it caps *new intake*,
not continuation. Lowering it mid-flight just stops new claims; existing
features finish.

### `WATCH_PATTERN` (default `prd/<your-slug>/*`)

Which PRD branches this harness claims. `<your-slug>` derives from
`git config user.email` (the part before `@`).

| Mode | Pattern | Behavior | When |
|------|---------|----------|------|
| **Per-dev (default)** | `prd/<my-slug>/*` | Each dev's harness claims only their own PRDs, on their own laptop, their own API quota. | Default. Best attribution, cost, and observability. |
| **Shared pool** | `prd/*/*` | All harnesses race for everything; atomic rename keeps it safe. | A team deliberately sharing a work pool. |

Note the glob: `*` matches one path component. Per-dev is `prd/alice/*`; shared
is `prd/*/*` (author component + feature component).

### STUCK caps

Bounded-retry circuit breakers — every step has one, so the loop can't run away.
At cap, the dispatcher signals STUCK on the PR (opening it as a draft if no PR
exists yet) with the session log + a diagnosis-first checklist for the human, and
halts that feature.

| Var | Default | Step it bounds |
|---|---|---|
| `PLANNING_CAP` | 2 | `/spec-planning` (skill crashes or never writes sentinel) |
| `VALIDATE_CAP` | 2 | `/spec-validate` (same) |
| `IMPLEMENT_CAP` | 3 | `/implement-mainspec` (PRD runner keeps failing) |
| `LOCAL_CHECKS_CAP` | 2 | `scripts/local-checks.sh` two-strike (auto-fix → focused LLM fix → STUCK) |
| `FEEDBACK_CAP` | 5 | reviewer feedback rounds |

All env-overridable in `.harness/env`. Raise for hard features; lower to fail
faster.

### `REVIEW_CLEAN_MARKER` (convergence signal)

Default `HARNESS_REVIEW_CLEAN`. When the reviewer has no Important findings left,
`REVIEW.md` instructs it to post a PR comment containing this token; the dispatcher
(`reviewer_converged`) sees it and hands the PR to the human for `/evaluate-pr` (it
writes `.harness/human-review-<f>`, posts the build-session trail once, and halts the
feature until the human merges/closes). Detection is intentionally simple — marker
present → converge, no freshness or author check. If the reviewer never posts it, the
feedback loop reaches `FEEDBACK_CAP` and STUCKs instead (a clean PR the human merges).
Set it **empty** in `.harness/env` when there is **no reviewer**, so the dispatcher
converges at PR-open. Must match whatever `REVIEW.md` tells the reviewer to post.

### Loop intervals (in the `/loop` invocations, not `.harness/env`)

There are **two** loops, each its own `/loop` session in the harness host worktree:

- `/loop 5m /poll-and-dispatch` — the **build loop** (features). `5m` is a sane
  default. Shorter = more responsive, more API ticks (most are cheap no-ops).
- `/loop 10m /learn-loop` — the **memory loop** (`/learn`). It can tick lazily: it
  only acts when `origin/main` has advanced past the `refs/harness/last-learned`
  watermark AND no `learn/<sha>` PR is already open. Most ticks are cheap no-ops.

Both are UX knobs, not correctness ones — the loops self-serialize (`flock`) and
re-derive their state every tick, so a missed or slow tick never corrupts anything.

### The memory loop's watermark (`refs/harness/last-learned`)

Not a `.harness/env` value — a git **ref** on the remote, the memory loop's only
durable state. It records how far into `main`'s history `/learn` has digested.
`learn-tick.sh` reads it as the `--since` for the next run and advances it (atomic
`--force-with-lease`) after each run. It lives in its own ref namespace, so it
survives `learn/<sha>` branch deletion and is shared across nodes — there is **no**
local `last-main-sha` file anymore. To force a full re-learn, delete the ref
(`git push origin :refs/harness/last-learned`) or run `/learn --rebuild` by hand.

### `WORKTREE_BASE` (rarely set)

Where per-feature worktrees are created: `${WORKTREE_BASE}-${feature}`. The
dispatcher derives the default from the **main worktree** name — `../<repo>-harness`
— so per-feature paths come out `../<repo>-harness-<feature>` regardless of which
worktree the dispatcher runs from. Override in `.harness/env` only if you want them
somewhere else (e.g. a different disk). Leave unset otherwise.

## What does NOT go in config

- **The claim mechanism** — it's the atomic rename, hardcoded. Not configurable.
- **Completion signals** — sentinel files, hardcoded in the dispatcher.
- **The pipeline order** — that's the `if/elif` chain in the script, edited
  directly (see dispatcher-explained.md), not a config value.
- **The host-worktree sync** — done by `scripts/harness-tick.sh` (the `/loop`
  target), not a config value. The loop must target the wrapper, not the dispatcher.

## The `.harness/` directory

Holds runtime state, all re-derivable, none of it secret:
- `env` — the config above (committed, or kept local — see below).
- `planning-attempts-<f>`, `validate-attempts-<f>`, `implement-attempts-<f>`,
  `local-check-attempts-<f>`, `feedback-rounds-<f>` — per-feature retry counters
  (each gates a STUCK circuit breaker).
- `stuck-<f>` (sentinel), `stuck-output-<f>.log` (tee'd failing output),
  `stuck-body-<f>.md` (the PR-body composed at STUCK) — written when a cap hits;
  cleared on merge/close.
- `human-review-<f>` (sentinel — reviewer converged, PR handed to the human),
  `human-review-posted-<f>` (marks the trail comment already posted, so it posts
  once), `human-review-body-<f>.md` (the "Ready for your review" comment) — written
  at convergence; cleared on merge/close.
- `sessions-<f>.tsv` — every `claude -p` invocation for this feature, one row each
  (timestamp, step, attempt, session_id, exit, duration). The STUCK PR body
  quotes the tail of this file so the human can open the trace by session_id.

**Counters and session logs must be gitignored.** They are per-node runtime state,
not project artifacts. harness-init adds `.harness/feedback-rounds-*`,
`.harness/local-check-attempts-*`, `.harness/implement-attempts-*`,
`.harness/planning-attempts-*`, `.harness/validate-attempts-*`,
`.harness/stuck-*`, `.harness/human-review-*`, `.harness/sessions-*.tsv`, and
`.harness/learn-review-body-*` to `.gitignore` (the memory loop's watermark is the
`refs/harness/last-learned` ref, not a file). Whether `.harness/env` is committed is a choice: commit it to
share defaults across a team's checkouts; keep it local (gitignored) if each
dev tunes their own. Recommend committing `env` and ignoring the counters.

## Multi-developer reminder

Per-dev is the default for a reason (attribution, cost isolation, "my harness is
my assistant" mental model). Don't steer a user to shared-pool unless they
explicitly describe a shared-queue workflow. When a team truly outgrows local
harnesses, the move is to transition to a server/CI harness — not to run many
local harnesses in shared-pool mode forever.

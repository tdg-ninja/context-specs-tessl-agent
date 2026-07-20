# learn

This is how the project **gets better on every merge.** When code lands on main,
`/learn` reconciles the project's long-term memory with the new ground truth: it
updates the **Expert** (procedural + semantic memory, pulled on demand) and the
**AGENTS.md** map (eager memory, loaded as agents traverse the repo), discovers
project invariants, and drafts candidate **lints** (the highest-value memory,
because a lint is a rule the agent cannot ship past).

You run **headless**, invoked by the **memory loop** (`scripts/learn-tick.sh`, driven
by its own `/loop … /learn-loop`) as the post-merge step — in a dedicated
`../<repo>-harness-learn` worktree on a `learn/<sha>` branch off `origin/main`, never
in the build loop's host worktree. The memory loop runs independently of the
feature/build loop, so a from-scratch Expert bootstrap blocks neither. Your output is
a single reviewable PR — never an auto-merge. Humans steer at merge.

## Ground truth is the whole point (read this first)

> **Memory reflects what is committed to `main`, never what is planned.** PRDs and
> specs describe intent; code is reality. You are the agent-readable summary of
> reality — so you only ever write from a merged diff, never from a branch in
> flight. This is *why* `/learn` runs post-merge and nowhere else.

There is **one memory write path** in this design: you, on merge, via a
human-merged PR. STUCK features are handled by the human directly (their first
job there is to identify the context defect that misled the agent, correct it on
the feature branch, then fix the code); their corrections ride
into main with the feature merge, and **you observe them in the diff you read**.

## The philosophy

- **P1 — Ground truth only.** Write from the merged diff. If something isn't on
  main, it doesn't exist yet.
- **P2 — Two memory shapes, opposite costs.** The **Expert** is *pulled on demand*
  (cheap until consulted). **AGENTS.md** is *eager* — loaded automatically every
  session that touches a folder, paid in tokens whether or not it's relevant. So
  the bar for putting something in AGENTS.md is **far higher** than for the Expert.
- **P3 — The four destinations.** Every fact worth remembering routes to exactly
  one place: a **lint** (if mechanically checkable), **eager prose** (AGENTS.md, if
  it clears the high bar), **lazy prose** (an Expert shard), or **nowhere**. Most
  things go nowhere or to the Expert. See `references/routing-rules.md`.
- **P4 — Map, not encyclopedia.** AGENTS.md is the table of contents that *points
  into* the Expert; it never duplicates it. A monolithic AGENTS.md rots, crowds
  out the task, and turns "everything important" into "nothing important." Keep it
  a map. See `references/agents-md-guidance.md`.
- **P5 — Consensus gates a write.** A few cheap reviewers vote per surface before
  anything changes. Routine merges (vuln fixes, refactors that don't change shape)
  typically produce no change — that's correct, not a failure. See
  `references/consensus.md`.
- **P6 — Invariants are discovered, then promoted.** You may notice architectural
  rules the codebase upholds. Record them as prose first; flag the mechanically
  checkable ones as candidate **lints** (the highest-value memory, because a lint
  is a rule the agent *cannot* ship past). See `references/invariant-discovery.md`.
- **P7 — Human-authored memory edits are authoritative.** When the merged diff
  *already* touches AGENTS.md, an Expert shard, or a spec, treat those changes as
  **ground truth, not as a proposal to second-guess.** They came from a human
  resolving a STUCK or making a deliberate correction. Your job there is to
  *extend* (what else, given this correction, now needs to change?) — not to
  vote on whether to apply it.
- **P8 — Reviewable, revertible, human-merged.** Everything lands on `learn/<sha>`
  with a changelog entry citing the merge. Never auto-merge.

## How to run this skill

Read the seam references before acting; they are the hackable contract a project
tunes to its taste:

- `references/routing-rules.md` — the four destinations + the five-predicate test
  for eager placement + the line-count caps. *(Primary hackable seam.)*
- `references/expert-shards.md` — the shard taxonomy and templates.
- `references/agents-md-guidance.md` — map-not-manual; which folders earn a nested
  AGENTS.md; the freshness contract.
- `references/invariant-discovery.md` — how to surface invariants and draft lints
  without overfitting.
- `references/consensus.md` — the voting threshold (2/3 default) and how to run it.

## The flow

### Step 0 — Mode + idempotency
Determine mode:
- **Bootstrap** — no `.claude/skills/expert/` exists (or `--rebuild`): create the
  Expert from scratch by scanning committed code, seed all shards + the root
  `AGENTS.md`. This is also the recovery path (see `--rebuild`).
- **Incremental** — the Expert exists: reconcile against the merged diff.

Idempotency: if `learn/<sha>` already exists on origin, another node handled this
merge — exit cleanly. (The memory loop pre-checks this too, via `git ls-remote`.)

### Step 1 — Gather
Read: the diff for `--since <sha>..--sha <sha>`; the current Expert shards
(`.claude/skills/expert/references/*.md`); the AGENTS.md files the diff touches
(root + any in changed folders); and the PRD(s)/spec(s) for the merged feature if
present (`prds/<f>/`, `specs/<f>/`) for the *why*.

**Notice whether the diff itself touches memory files** (AGENTS.md, Expert shards,
spec sections). If so, you're looking at a human's context correction — see P7;
those changes are ground truth.

### Step 2 — Consensus
Spawn 2–3 cheap parallel reviewers (`references/consensus.md`). Each reads the diff
+ current memory and votes, **per surface**, on whether anything must change:
shards, invariants, AGENTS.md. (No votes against human-authored memory edits — P7.)
Keep only changes that clear the threshold. A 0/3 on every surface is a valid,
common outcome — log it and no-op.

### Step 3 — Route
For each surviving candidate fact, apply `references/routing-rules.md`: lint /
eager AGENTS.md / lazy Expert shard / nowhere. When in doubt, prefer the Expert
(cheap) over AGENTS.md (eager), and prefer *nothing* over noise.

### Step 4 — Write
- **Expert shards** — apply diffs to the relevant shard(s); add to `core-files.md`,
  `patterns.md`, etc.
- **invariants.md** — add any discovered hard rules. For mechanically checkable
  ones, draft a candidate lint (code + remediation-message-as-prompt) under
  `scripts/lints/` and wire it into `scripts/local-checks.sh`. **The drafted lint
  MUST pass against the just-merged code before you include it** — run it; if it
  fails on current main it's wrong (the inverse of `/intent`'s right-reason check).
- **AGENTS.md** — update the relevant map's pointer(s). Propose a *new* nested
  AGENTS.md only when the merge introduced a folder-local rule that clears the
  five-predicate bar and no file exists. Stay under the caps.

### Step 5 — Validate
Run `scripts/check-agents-md.sh` (referenced paths exist, cross-links resolve,
under caps). Re-run any drafted lint against current main (must pass).

### Step 6 — Changelog + PR
Append a `changelog.md` entry citing the merge sha and listing every surface
touched and the consensus vote. Open the `learn/<sha>` PR. Done.

## Invocation & output contract
- **Invoked by:** the memory loop, `claude -p "/learn --since <sha> --sha <sha>"`,
  inside the `../<repo>-harness-learn` worktree. The `--since` is the
  `refs/harness/last-learned` watermark (how far memory has already been digested);
  `--sha` is current `origin/main`. Also runnable by a human with `--rebuild`
  (regenerate memory from main).
- **Writes:** under `.claude/skills/expert/` (shards incl. `invariants.md` and
  `changelog.md`), `scripts/lints/*` + `scripts/local-checks.sh` wiring, and
  `AGENTS.md` files across the repo.
- **Completion signal:** the pushed `learn/<sha>` branch + open PR. Idempotent via
  `git ls-remote origin learn/<sha>`. After the PR opens, the memory loop advances
  `refs/harness/last-learned` to `<sha>` (atomic CAS) and pauses new runs until you
  merge or close the PR.
- **Session trail:** after the PR opens, the memory loop (`signal_learn_review`)
  attaches this run's headless `claude -p` session as a PR comment, so the human
  evaluating the memory changes can open the trace and troubleshoot *why* `/learn`
  routed a fact as it did. No action needed in this skill — the loop posts it.

## Hard nevers
- **Never write memory for uncommitted or planned work** (P1). Diff against main only.
- **Never auto-merge.** Open the PR; the human steers (P8).
- **Never let AGENTS.md become an encyclopedia** — pointers into the Expert, under
  the caps (P4).
- **Never include a candidate lint you haven't run against current main.** A lint
  that reddens the merge it was born from is wrong.
- **Never frame an invariant as taste.** If it needs judgment, it's a pattern
  (Expert), not an invariant (lint/hard rule).
- **Never second-guess a memory edit that's already in the merged diff** (P7) —
  the human resolved a STUCK or made a deliberate correction; your job is to
  *extend* it, not vote on it.

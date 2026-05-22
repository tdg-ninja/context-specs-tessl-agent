---
name: capture-lesson
description: Capture one episodic lesson from a feature that got STUCK, so the project learns from struggle even when the work never merges. Single-agent and cheap. Judges whether the failure is generalizable, writes NOTHING for flakes/env/bad-PRD failures, and otherwise appends one dated, attributed lesson to the Expert's lessons.md on a rolling memory PR. Triggers - capture lesson, learn from failure, record lesson, post-stuck (project)
---

# capture-lesson

The richest learning comes from the struggle — and most struggle never merges.
`/learn` only fires post-merge, so a feature that goes STUCK (the PRD runner keeps
failing, local checks won't pass, the feedback loop hits its cap) would teach the
project nothing. This skill closes that gap: when the dispatcher flags a terminal
STUCK, you capture **one** lesson from what went wrong.

You run **headless and single-agent** — this is a cheap proposal, not a blessing.
You only ever **append**; `/learn` (Path A) is the only thing that curates, blesses,
or retires memory. Path B proposes; Path A disposes.

## The bar: most failures are NOT lessons (read this first)

> **Write nothing unless the failure teaches something generalizable.** A flaky
> test, a missing dependency, an environment hiccup, a typo, or a simply-bad PRD
> are *not* lessons — they're noise, and a false lesson poisons every future
> session that reads it. When in doubt, **write nothing and exit 0.** Restraint is
> the default; a captured lesson is the exception.

## The philosophy
- **P1 — Generalizable or nothing.** Ask: "would this lesson help a *different*
  feature avoid the same wall?" If not, exit without writing.
- **P2 — Reason, not prohibition.** "X failed because Y" — never "never do X." A
  reason can be re-evaluated when the codebase or model changes; a flat ban can't,
  and becomes stale scaffolding that holds the project back.
- **P3 — Dated and attributed, always.** Every lesson carries the date, the
  feature, the branch sha, and what tripped (which STUCK). Attribution is what lets
  a human later trace a strange steering decision back to its source.
- **P4 — Append only; one lesson.** You add a single entry. You never edit/retire
  existing lessons, never touch shards/invariants/AGENTS.md — that's `/learn`.
- **P5 — Human-merged, like all memory.** Your output is a rolling memory PR a
  human reviews. No auto-merge.

## The flow

### Step 0 — Gather the evidence
You're invoked as `/capture-lesson <feature>`. Read the struggle:
- `git log feature/<feature>` (and diffs) — what was tried and re-tried.
- `.harness/` counters for this feature: `implement-attempts-<f>`,
  `local-check-attempts-<f>`, `feedback-rounds-<f>`, and which `stuck-<f>` fired.
- `prds/<feature>/prd.md` + the runner's last output, and `specs/<feature>/` if present.

### Step 1 — Judge (the bar)
Decide: is the failure **generalizable** (a real property of this codebase/domain a
future feature would hit) or **noise** (flake / env / dependency / typo / the PRD
itself was wrong)? If noise → log one line saying so and **exit 0 without writing**.

### Step 2 — Distill one lesson
If generalizable, write exactly one entry per `references/lesson-format.md`: dated,
attributed, framed as a reason. Keep it tight — one wall, one why.

### Step 3 — Append on the rolling memory branch
- Target file: `.claude/skills/expert/references/lessons.md`. If the Expert doesn't
  exist yet (a feature went STUCK before the project's first merge), create
  `lessons.md` (and a minimal `.claude/skills/expert/SKILL.md` stub so the skill is
  valid) — the first `/learn` will fold it into the full Expert.
- Use the standing branch `learn/lessons`: fetch + rebase it onto `origin/main`
  first (you touch only `lessons.md`, so conflicts are nearly impossible), append,
  commit, push.
- Open the PR if absent, or let the existing open PR pick up the new commit. This
  is the one rolling "memory" PR a human merges periodically.

## Invocation & output contract
- **Invoked by:** the dispatcher, `claude -p "/capture-lesson <feature>"`, once per
  STUCK feature (idempotency enforced by the dispatcher's `lesson-captured-<f>`
  marker).
- **Writes:** at most one appended entry to `.claude/skills/expert/references/lessons.md`
  on the `learn/lessons` branch. Often writes nothing (that's success).
- **Completion signal:** either "no lesson (noise)" logged, or a commit pushed to
  `learn/lessons` + its PR open/updated.

## Hard nevers
- **Never write a lesson for a flake, env issue, missing dep, typo, or bad PRD** (P1).
- **Never frame a lesson as a prohibition** — always the reason (P2).
- **Never write without date + feature + sha + what-tripped** (P3).
- **Never edit or retire existing lessons, or touch any other memory surface** —
  shards, invariants, AGENTS.md, and curation all belong to `/learn` (P4).
- **Never auto-merge** the memory PR (P5).

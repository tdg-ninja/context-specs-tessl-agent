# Outcomes: where the changes land

This is the plumbing behind Step 6. The skill produces two kinds of artifact — **evals**
(`evals/<name>/`) and **context fixes** (Expert / AGENTS.md / a skill) — and the only
question this file answers is *where do they get committed*. The answer is always **a
branch, never `main`**, and `/learn` writes memory from the merge.

> Governing contract: **there is one memory write path in this design — the project's memory
> updater (`/learn`) runs only on merge to `main`, from ground truth.** This skill never writes
> `main` and never writes memory autonomously. It authors edits on a branch; the merge carries
> them to `main`; when `/learn` then reads the merged diff it treats human-authored memory edits
> as ground truth to *extend*, not second-guess — the same path a memory edit a human seeds
> during PR review, or a STUCK context correction, already takes.

## Why a branch, not a direct edit

Two reasons, both load-bearing:

1. **Ground truth.** Memory reflects what's on `main`. An edit you make in your checkout
   isn't real until it merges — writing it straight to the Expert would record a *proposal*
   as if it were *reality*, which the project's ground-truth rule forbids (memory describes
   committed code, never planned work).
2. **Reviewable + revertible.** Every memory change rides a PR a human merges. Your
   eval/context edits inherit that: they land on a branch, get merged deliberately, and the
   post-merge memory pass reconciles the rest.

## Where in the project a context fix is written

You route the fix to a destination in SKILL.md's S9 (lint / AGENTS.md / Expert shard /
nowhere). To find the exact file, read the **project's own** artifacts — not any skill's
internals:

- **Expert shard** — open `.claude/skills/expert/references/` in the project and pick the shard
  whose subject matches (architecture, verification, patterns, procedural, core-files,
  invariants). If none fits and the fact is real, the project's memory updater can place it on
  its post-merge pass; your job is to write a clear, correctly-scoped note in the closest shard.
- **AGENTS.md** — the root `AGENTS.md`, or the nested one in the folder the rule is local to.
  Only if it clears the five-predicate bar (S9); otherwise prefer the Expert.
- **A skill defect** — if a *skill's own text* steered the agent wrong, the fix is that skill's
  `SKILL.md` (or its `references/`). Edit it like any other context, on the branch.
- **A lint** — add the check under the project's `scripts/lints/` and wire it into
  `scripts/local-checks.sh`; it must pass against current code before it's included.

## Path A — add to the PR being reviewed (default)

Use when the PR is going to **merge** (a HUMAN_REVIEW build-audit, or a STUCK you're about to
resolve). Put the eval/context changes on the PR's own branch so they ride in with it.

The harness's per-feature worktree still holds the branch, and git refuses the same branch in
two worktrees — so commit from a **detached checkout** of the PR head, exactly like
`/evaluate-pr`:

```bash
git fetch origin
git checkout --detach origin/<branch>          # feature/<f> or learn/<sha>

# ... author evals/<name>/ and/or the Expert/AGENTS.md/skill edits, with the human ...
# ... run evals/<name>/run-eval.sh: RED before the context fix, GREEN after (right-reason) ...

git add -A
git commit -m "eval+context: <what the trail revealed, in one line>"
git push origin HEAD:<branch>                  # detached HEAD -> push to the branch ref
```

For a `feature/<f>` PR the reviewer re-runs on the push; the human merges when ready. For a
`learn/<sha>` PR you're auditing, the same — your additions ride that PR into `main`.

## Path B — fresh capture branch (the discard case, S6)

Use when the human will **close** the PR but still wants the learnings. `/learn` never runs
without a merge to `main`, so a learning attached only to a doomed PR dies with it. Land it
on its own branch instead, off clean `main`, carrying **only** the eval/context changes —
nothing from the discarded work:

```bash
git fetch origin
git checkout --detach origin/main
git switch -c capture/<slug>                   # <slug>: short, describes the learning

# ... author evals/<name>/ and/or the context edits, with the human ...
# ... run-eval.sh RED-before / GREEN-after ...

git add -A
git commit -m "capture: <learning from the discarded PR>, in one line"
git push -u origin capture/<slug>
gh pr create --base main --head capture/<slug> \
  --title "capture: <learning>" \
  --body "Learnings salvaged from #<original-pr> (being closed): <two lines>."
```

Then the human can close the original PR freely:

```bash
gh pr close <original-pr> --comment "Closing; learnings captured in #<capture-pr>."
```

The capture PR is small, reviewable, and merges on the human's call — at which point
`/learn` picks up the memory edits as ground truth like any other merge.

## Choosing the path

It's the human's explicit call, framed by the PR's fate — confirm it in Step 6:

| The PR will… | Path | Why |
|---|---|---|
| **Merge** (you're resolving STUCK, or auditing a converged PR you'll keep) | **A** — add to the PR | Changes ride in with the work; one merge, one `/learn` pass. |
| **Be discarded** (wrong approach, but you learned something) | **B** — capture branch | The learning outlives the closed PR. |

When unsure, ask: *"are we keeping this PR?"* The answer picks the path.

## Always return

End on `main`, like `/evaluate-pr`:

```bash
git checkout main
```

Never leave the user on a detached HEAD or a capture branch.

## Hard nevers (echoing SKILL.md)

- Never commit eval/context changes to `main` directly — always a branch.
- Never auto-merge — the human merges.
- Never write the Expert/AGENTS.md *autonomously* — only edits the human agreed to, on a
  branch, captured *with* them.
- Never edit `prds/<f>/prd.md` — the spec of record is off-limits here.

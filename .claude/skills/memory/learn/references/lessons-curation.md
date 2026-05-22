# Lessons curation

**Hackable seam.** `/learn` (Path A) is the **garbage collector** of episodic
memory. `/capture-lesson` (Path B) appends raw, provisional lessons from failures;
you reconcile them against ground truth on each merge. Path B proposes; you dispose.

## What lessons.md is for
Negative, episodic knowledge consulted by future reasoning: "X failed because Y —
don't reach for X here." It is *not* an audit log (that's `changelog.md`).

## Each lesson's required shape (also see capture-lesson/references/lesson-format.md)
- **Dated** and **attributed** (which feature, branch sha, what tripped — STUCK on
  PRD runner / local checks / feedback cap).
- Framed as a **reason, not a prohibition**: "client-side search failed because the
  `?q=` URLs must be crawlable (SSR)" — *not* "never use client-side search." A
  reason can be re-evaluated when the codebase changes; a prohibition can't.

## Your curation operations (on every merge)
1. **Dedup / merge.** Collapse near-identical lessons into one with the strongest
   reasoning.
2. **Retire on contradiction.** If *this* merge demonstrates that a standing lesson
   is now false (e.g. a feature merged that successfully does the thing a lesson
   warned against), **remove it** — ground truth invalidates a stale warning. This
   is the single most important curation step; without it `lessons.md` rots into a
   pile of contradictions that mislead `/intent` and `/spec-planning`.
3. **Prune the obvious.** If a lesson's content is now plainly inferable from the
   merged code, archive it — it's earning its keep no longer.
4. **Keep attribution.** Never strip the date/sha — it's what lets a human trace a
   weird steering decision ("why did `/intent` stop suggesting X?") back to its
   source. Observability is the guard against invisible, compounding steering bugs.

## Note the two write-paths in changelog
When you curate lessons, record it in `changelog.md` like any other surface (which
lessons retired/merged, and why). The lessons themselves stay in `lessons.md`; the
*record of curating them* is provenance.

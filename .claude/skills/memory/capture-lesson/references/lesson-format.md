# Lesson format

One lesson = one entry appended to `.claude/skills/expert/references/lessons.md`.
Shared shape with `/learn`'s curation (see `memory/learn/references/lessons-curation.md`).

## Template

```markdown
## <YYYY-MM-DD> — <feature> (sha <short-sha>, STUCK: <which-gate>)
**What was tried:** <the approach that hit the wall, in one or two lines>
**Why it failed:** <the reason — the generalizable property, not the symptom>
**For next time:** <what a different feature should consider instead>
```

## Worked example (good)

```markdown
## 2026-05-21 — search-autocomplete (sha 9f3c2a1, STUCK: PRD runner 3x)
**What was tried:** client-side fetch of results on keypress against /api/search.
**Why it failed:** the PRD requires crawlable result URLs (?q=...), which need SSR;
the route rendered nothing in view-source, so the runner's SSR check never passed.
**For next time:** query-param result pages in this app must be server-rendered —
see the SSR pattern the expert records for /posts.
```

## Why these fields

- **Date + feature + sha + gate** = attribution (P3). Lets a human trace a steering
  decision back to its origin, and lets `/learn` later reconcile it against a merge.
- **"Why it failed" is the reason, not the symptom** (P2). "Runner exited 1" is a
  symptom; "result URLs must be crawlable, which needs SSR" is the reason a *future*
  feature can act on. A reason can be re-evaluated; a symptom or a ban cannot.

## What is NOT a lesson (write nothing)
- Flaky/non-deterministic test failure.
- Missing dependency, unconfigured env var, port conflict, secret not copied.
- A typo or a transient tooling error.
- The PRD itself was wrong/contradictory (that's feedback on the PRD, not a durable
  property of the codebase).

If the struggle reduces to one of these, log one line ("no durable lesson: flaky
integration test") and exit without appending.

# release-notes

Draft release notes from merged PRs or a git range.

## 1. Identify the source

Use the source named by the maintainer:

- **Merged PRs** — collect the requested PR numbers, release milestone, label, author, or time window.
- **Git range** — use the requested range, tag pair, or last release tag through `HEAD`.
- **Unclear source** — ask for the range, release, or PR set before drafting.

## 2. Collect evidence

Gather enough evidence to summarize impact without reading unrelated history:

- PR titles, bodies, labels, authors, linked issues, review notes, and merge dates.
- Commit subjects and merge commits in the range.
- Changed-file context for ambiguous work.
- Existing changelog or release-note style if the repo has one.

## 3. Triage content

Group related PRs and commits into one note when they describe the same change.
Ignore merge noise, formatting-only changes, and duplicate commits unless they affect users.
Separate user-facing changes from docs, tests, dependencies, CI, harness, and maintenance work.

## 4. Draft format

Write a concise markdown draft with these sections:

```md
# Release notes draft

## Highlights

## Changes

## Fixes

## Internal / harness changes

## Upgrade notes
```

Use short bullets. Include PR numbers or commit refs when available. Write `None noted` for empty sections only when useful to make the draft complete.

## 5. Publication readiness

Mention uncertainty only when the evidence is incomplete or contradictory.
End with follow-up questions for anything a maintainer must decide before publishing.

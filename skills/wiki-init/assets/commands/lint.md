---
description: Health-check the wiki — find broken links, orphans, stale claims, contradictions, frontmatter drift, and suggested new pages. Writes a timestamped report; --fix auto-applies safe categories only.
argument-hint: [--scope=all|concepts|sources|links] [--fix]
---

# /lint

Read `CLAUDE.md` first for the layered structure, page taxonomy, frontmatter contract, and hard rules.

Arguments: `$ARGUMENTS`

Parse from `$ARGUMENTS`:
- `--scope=all|concepts|sources|links` — narrow which checks run (default: `all`).
- `--fix` — auto-apply **safe** fixes only (broken-link renames where the target is unambiguous, frontmatter normalization, trivial backlinks). All non-safe findings remain as suggestions in the report.

## Step 1 — Build the link graph

Walk `wiki/` and read every markdown page. For each page extract:
- Path, slug, frontmatter (`type`, `title`, `created`, `updated`, `status`, `tags`, `sources`, `aliases`, `raw_path` if source).
- All `[[wikilinks]]` (outgoing edges).
- Headers and section structure.

Build:
- A `slug → page` map (note duplicate slugs across folders if any — that's a warning).
- An alias map: `alias → slug`.
- An adjacency list (outgoing) and reverse-adjacency (incoming = backlinks).

## Step 2 — Run checks

Run these unless filtered out by `--scope`:

### Broken links (`scope: links` or `all`)
For every `[[target]]` in every page, check `target` resolves to an existing slug or a known alias. If not, flag.
- **Safe-fix**: if the target is a near-miss of exactly one existing slug (Levenshtein ≤ 2 or singular/plural mismatch), `--fix` rewrites the link.
- Otherwise, suggest in the report.

### Orphans (`scope: concepts` or `all`)
A page is an orphan if no other page links to it. Exclude `wiki/MOC.md` and pages under `wiki/indexes/`. Source-summary pages (`type: source`) are also exempt — they're entry points for raw content, not nodes the wiki is required to reach.

### Missing backlinks (`scope: links` or `all`)
If page A's body or Related section links `[[B]]`, and B's "Related" section does **not** mention `[[A]]`, flag as a missing reciprocal link. Heuristic — surface for review.
- **Safe-fix**: with `--fix`, append `[[A]]` to B's Related list if and only if both pages are concept/entity/workflow type and A is the only missing reciprocal.

### Stale claims (`scope: concepts` or `all`)
If a page's `updated:` date is older than the most recent `created:` of any source listed in its `sources:`, flag — the page may be missing claims from a newer source. Surface for review only; do not auto-fix.

### Contradictions (`scope: concepts` or `all`)
Group pages by topic clusters (heuristic: pages that share ≥2 incoming/outgoing links). For each cluster of ≤8 pages, read them and look for assertions about the same subject that disagree. Report each as: subject, page A claim, page B claim, suggested resolution. Never auto-fix.

### Frontmatter drift (`scope: all`)
For every wiki page check the frontmatter contract from `CLAUDE.md`:
- All required keys present: `type`, `title`, `created`, `updated`, `status`, `tags`, `sources`, `aliases`.
- `type` is one of the five valid values and matches the folder (`type: concept` lives under `wiki/concepts/`, etc.).
- `status` is one of `stub | draft | stable`.
- `created` and `updated` parse as YYYY-MM-DD; `updated` ≥ `created`.
- Source pages additionally have `raw_path:` pointing to a file that exists under `raw/`.
- **Safe-fix**: with `--fix`, normalize key order, add missing keys with reasonable defaults (`tags: []`, `aliases: []`, `sources: []`, `status: draft`). Never invent a `title` or override an existing value.

### Suggested new pages (`scope: concepts` or `all`)
- Concepts mentioned by name (or alias) ≥3 times across the wiki without their own page → suggest creating one.
- Entities (proper-noun tools/people/products) referenced in concept/workflow pages without their own entity page → suggest creating one.
- Source claims that don't appear absorbed in any concept/entity/workflow page → suggest where they should land.

### Unabsorbed source claims (`scope: sources` or `all`)
For every `wiki/sources/*.md`, check that each "Claims extracted" bullet links a wiki page that actually contains that claim (or a paraphrase). If a bullet lists no `[[wikilink]]` or its linked page doesn't reference the source, flag.

### Duplicate / near-duplicate pages (`scope: concepts` or `all`)
Two pages with very similar titles, alias overlap, or near-identical opening paragraphs are likely a fold candidate. Surface for review; never auto-merge.

## Step 3 — Write report

Create `_meta/lint-reports/<YYYY-MM-DD-HHMM>.md`:

```markdown
---
type: index
title: "Lint Report YYYY-MM-DD HH:MM"
created: <today>
updated: <today>
status: stable
tags: [lint-report]
sources: []
aliases: []
---

# Lint Report — <timestamp>

Scope: <scope>. Fix mode: <on|off>.

## Summary

| Category | Findings | Auto-fixed |
|---|---|---|
| Broken links | N | M |
| Orphans | N | 0 |
| Missing backlinks | N | M |
| Stale claims | N | 0 |
| Contradictions | N | 0 |
| Frontmatter drift | N | M |
| Suggested new pages | N | 0 |
| Unabsorbed source claims | N | 0 |
| Duplicate candidates | N | 0 |

## Findings

### Broken links

- `wiki/concepts/foo.md`: `[[bar]]` → no such slug. Did you mean `[[baz]]`? <auto-fixed | suggested>
- ...

### Orphans

- `wiki/concepts/foo.md` — no inbound links. Suggested home: link from [[index-x]] or absorb into [[bigger-concept]].

<sections continue for each category, only those with findings>
```

If a category has zero findings, omit its section.

## Step 4 — Apply safe fixes (if `--fix`)

Apply only the fixes flagged "auto-fixed" above:
- Broken-link rewrites with unambiguous near-miss targets.
- Frontmatter normalization (add missing optional keys with empty defaults; reorder keys).
- Reciprocal Related-list backlinks where exactly one direction is missing.

After applying, bump `updated:` on every modified page to today.

Never auto-fix:
- Stale claims (need human judgment about what new info to fold in).
- Contradictions.
- Suggested new pages.
- Duplicate-merge candidates.
- Unabsorbed source claims (placement requires synthesis).

## Step 5 — Report to user

Print:
- Path to the lint report.
- Top-line summary (counts).
- If `--fix` was used: count of pages auto-modified.
- Top 3 most actionable suggested follow-ups (e.g. "create entity page for [[some-tool]]", "fold contradiction in [[concept-a]] vs [[concept-b]]").

## Constraints

- The lint pass is **read-only by default**. `--fix` is the only mode that writes, and only to safe categories.
- Never delete a page during lint.
- Never auto-create a suggested page — only suggest.
- The report itself counts as a lint artifact, not a wiki page; it lives under `_meta/lint-reports/` and is excluded from orphan checks.

---
description: Ingest a raw source (file path or URL) into the wiki — read the source, extract concepts/entities/workflows/claims, then create or update wiki pages with cross-links and citations.
argument-hint: <path-or-url> [--type=transcript|article|tweet|gist|repo-notes] [--yolo]
---

# /ingest

You are extending an LLM-maintained wiki at the project root. Read `CLAUDE.md` first for the layered structure, page taxonomy, frontmatter contract, and hard rules. **You must obey those rules.** In particular: never modify `raw/` (except to save a URL fetch), every wiki claim must cite a `[[source]]`, prefer updating existing pages over creating near-duplicates, and rewrite (don't just append) when a new source supersedes an old claim.

Arguments: `$ARGUMENTS`

Parse from `$ARGUMENTS`:
- **Required**: a file path under `raw/` *or* a URL.
- **Optional**: `--type=transcript|article|tweet|gist|repo-notes` (auto-detect from path/URL/content if absent).
- **Optional**: `--yolo` — skip the plan-pass approval step.

If `$ARGUMENTS` is empty or unparseable, ask the user for the source path/URL and stop.

## Step 1 — Resolve the source into `raw/`

Two cases:

**A. File path**: must already live under `raw/`. If it's a path outside `raw/`, refuse and tell the user to move it under the right `raw/` subfolder first (transcripts/articles/tweets/gists/repos).

**B. URL**: fetch the content (use WebFetch). Pick a destination based on `--type` or the URL shape:
- gist.github.com → `raw/gists/<slug>.md`
- twitter.com / x.com → `raw/tweets/<slug>.md`
- otherwise → `raw/articles/<slug>.md`

The slug is a kebab-case derivative of the title or URL path. Save the fetched content with this frontmatter at the top:

```yaml
---
source_url: <full URL>
fetched_at: <YYYY-MM-DD>
type: <transcript|article|tweet|gist|repo-notes>
---
```

This is the **only** time you write under `raw/`.

## Step 2 — Read the source fully

Use Read on the resolved `raw/...` path. Read the whole document (use multiple Read calls if necessary; do not truncate).

## Step 3 — Extract

Build an internal scratch list. For each item, decide which page type it belongs to:

- **Concepts**: ideas, techniques, distinctions, named patterns. Each becomes (or updates) a `wiki/concepts/<slug>.md`.
- **Entities**: people, orgs, tools, products, repos, protocols, regulations. Each becomes (or updates) a `wiki/entities/<slug>.md`.
- **Workflows**: practices with steps, multi-step procedures. Each becomes (or updates) a `wiki/workflows/<slug>.md`.
- **Claims**: specific factual or evaluative assertions. Each will appear in the source-summary's "claims extracted" list and get folded into the relevant concept/entity/workflow page.
- **Open questions**: things the source raises but doesn't answer. These go in the "Open questions" section of relevant pages.

For each candidate item, pick a stable kebab-case slug.

## Step 4 — Reconcile against existing wiki

For each candidate slug, check if a page already exists:

```
ls wiki/concepts/<slug>.md  wiki/entities/<slug>.md  wiki/workflows/<slug>.md  2>/dev/null
```

Also Grep `wiki/` for the slug appearing in `aliases:` frontmatter — an existing page may be the right home under a different name. If so, route the claim to that page. If a new source **supersedes** a claim on an existing page, plan a rewrite (update the live claim, preserve the old version as a dated note), not a blind append.

## Step 5 — Plan pass

Emit a concrete change plan to the user:

```
INGEST PLAN — <source slug>

NEW pages (n=K):
  wiki/concepts/<slug>.md      (Title)
  wiki/entities/<slug>.md      (Title)
  ...

UPDATES (n=M):
  wiki/concepts/<existing>.md  — fold in claim about X; add cross-link to [[new-slug]]
  ...

CROSS-LINKS (n=L):
  [[a]] ↔ [[b]]
  ...

SOURCE SUMMARY:
  wiki/sources/<source-slug>.md  (will list ~N claims)

MOC update:
  add new top-level entries under <category>
```

Then **stop and wait for approval**, unless `--yolo` was passed. The user may reply with edits ("merge X and Y", "drop Z", "rename foo → bar"). Apply the edits, re-emit the plan, and wait again. Loop until approved.

## Step 6 — Write pass

Once approved (or `--yolo`), execute the plan as a batch. Every write must conform to the frontmatter contract in `CLAUDE.md`.

**Source summary** (`wiki/sources/<source-slug>.md`):

```markdown
---
type: source
title: "Human Title of the Source"
created: <today>
updated: <today>
status: stable
tags: [...]
raw_path: raw/.../<file>
sources: []
aliases: []
---

# Human Title of the Source

<200–500 word neutral summary of what the source is and what it covers.>

## Claims extracted

- Claim phrased in one sentence → absorbed in [[concept-slug]]
- Another claim → absorbed in [[entity-slug]] and [[workflow-slug]]
- ...

## Open questions

- Things the source raises but doesn't fully answer.
```

**New concept/entity/workflow pages** follow the body shape from `CLAUDE.md`:

1. Definition (1–3 sentences)
2. Why it matters
3. Mechanics
4. Examples — each cites `[[<source-slug>]]`
5. Related: bulleted `[[wikilinks]]`
6. Open questions

Frontmatter must include `sources: ["[[<source-slug>]]"]`. Set `status: draft` for newly created pages (promote to `stable` only on a later pass when the page has 2+ sources or has been reviewed).

**Existing-page updates**:
- Append claims into the most natural section. Don't blindly tack on a "From [[x]]" subsection unless the claim doesn't fit anywhere existing — prefer to fold it into Mechanics or Examples with a `[[<source-slug>]]` citation inline.
- If the new source supersedes a prior claim, **rewrite** the live text and move the superseded version into a dated "Previously" note rather than leaving both unmarked.
- Bump `updated:` to today.
- Append the new source to `sources:` if not already present.
- If the new source supports cross-linking to a new sibling page, add a bullet under Related.

**MOC** (`wiki/MOC.md`): add any new top-level concept/entity/workflow under the appropriate category section. Don't list every page — MOC curates.

## Step 7 — Append to ingest log

Append one block to `_meta/ingest-log.md`:

```markdown
## <YYYY-MM-DD HH:MM> — <source-slug>

- Source: `raw/.../<file>` (<type>)
- New pages: <count> (list paths)
- Updated pages: <count> (list paths)
- Cross-links added: <count>
```

## Step 8 — Report

Print a final summary to the user with:
- The source-summary path
- Bulleted list of new pages
- Bulleted list of updated pages
- Suggested next step (e.g., "run /lint to verify cross-links" or "consider ingesting <related URL>")

## Constraints

- **Read `wiki/` only when reconciling**, not to absorb wiki content into your synthesis. Synthesis is from the raw source.
- Never duplicate a page that exists under a different slug — search aliases first.
- If a claim has no clear home, prefer creating a stub concept page (`status: stub`) over leaving the claim only in the source summary.
- Keep wiki pages concise. The wiki is a network of small, well-cited nodes — not a re-typing of the source.

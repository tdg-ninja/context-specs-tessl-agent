---
description: Ask a question against the wiki. Reads MOC.md for topology, greps wiki/ for keywords, follows wikilinks 2 hops, returns an answer with [[wiki-slug]] citations on every claim. Offers post-hoc promotion to wiki/inbox/ when the answer is novel.
argument-hint: <question>
---

# /query

Read `CLAUDE.md` first for the layered structure and hard rules. **Critical rule for this command**: search `wiki/` only — never read from `raw/`. Synthesis-at-ingest is the whole point of the wiki; if a question can't be answered from `wiki/`, the right answer is "ingest more sources," not "let me go read the raw docs."

Arguments: `$ARGUMENTS`

The argument is the natural-language question. If `$ARGUMENTS` is empty, ask the user for their question and stop.

## Step 1 — Topology pass (read MOC first)

Before grepping, read `wiki/MOC.md` end-to-end. MOC is the curated map of the vault — it tells you which clusters/sections exist and which pages are considered canonical entry points for each area. Note which sections are most relevant to the question; you'll use them to weight grep results in step 2 and to notice gaps (e.g. "MOC has no section that covers this question — that itself is a finding").

If MOC obviously hasn't been updated for pages you encounter later (e.g. step 2 surfaces a clearly-relevant page that MOC doesn't link), flag this in your final answer as a lint-worthy finding so the user knows MOC is drifting.

## Step 2 — Find the seed pages

Identify keywords/concepts in the question. Use Grep over `wiki/` (NOT `raw/`) to find candidate pages. Match against:
- Filenames (slugs).
- H1 titles.
- `aliases:` frontmatter values.
- First paragraph / Definition section text.

Score candidates by:
1. How directly the page addresses the question (keyword density, definition match).
2. Whether MOC lists it under a section the question maps to (boost).

Take the top ~5 as seed pages.

## Step 3 — Walk the link graph (2 hops)

For each seed page, read it. Follow outgoing `[[wikilinks]]` to add neighbors to the working set. Then follow links one more hop. Cap the working set at ~15 pages — beyond that, the question is too broad, narrow it.

While reading, note:
- Which pages contain claims relevant to the question.
- Which sources (`[[<source-slug>]]`) those claims cite.
- Any contradictions or open questions surfaced by the pages.

## Step 4 — Compose the answer

Write a direct answer in prose. Rules:

- **Every non-trivial claim must inline-cite a `[[wiki-slug]]`** — the wiki page where that claim is grounded. The reader can click through in Obsidian to the wiki page, and from there to its `[[<source-slug>]]` and on to the raw doc if they want.
- Keep it concise. Match the depth of the question — a yes/no question gets 2–3 sentences; a "compare X and Y" gets a short paragraph with both sides cited.
- If the wiki contradicts itself on the point in question, surface that explicitly: "[[a]] and [[b]] disagree on this — [[a]] says X, [[b]] says Y." Don't paper over it.
- If a claim you'd want to make has **no citation available** in the wiki, do **not** invent one. Either:
  1. Drop the claim, or
  2. Make it explicitly: "The wiki doesn't cover this. Consider running `/ingest <suggested-source>` to fill the gap."

End with a **Sources consulted** list of the wiki pages you read (not raw sources — those live behind the wiki citations).

## Step 5 — Offer promotion (only when novel)

After printing the answer, judge whether it is **promote-worthy**. An answer is promote-worthy when it *synthesizes* across multiple pages into a view that doesn't already exist as its own wiki page — i.e. a future reader asking the same question would benefit from a standing page rather than re-running the query.

Heuristics:
- **Promote-worthy**: pulled threads from 3+ pages, surfaced a contradiction, framed a comparison, or distilled a workflow that's only implicit in the existing pages.
- **Not promote-worthy**: the answer is essentially "see [[page-x]]" — a single existing page already covers it. A quick factual lookup. A meta-question about the wiki itself.

If promote-worthy, end your response with a single-line offer like:

> *This pulls threads from N pages — promote to `wiki/inbox/<slug>.md`?*

Then **stop and wait**. Do not write the file. The user replies (e.g. "yes", "promote it", "no") in the next turn.

If not promote-worthy, do not offer — just end with the Sources consulted list.

## Step 6 — Promote on confirmation

If the user confirms promotion (in a follow-up turn), write the answer to `wiki/inbox/<question-slug>.md` where `<question-slug>` is a kebab-case rendering of the question's core noun phrase (≤6 words).

Frontmatter:

```yaml
---
type: concept   # or index, depending on shape
title: "Question phrased as a title"
created: <today>
updated: <today>
status: draft
tags: [from-query]
sources: ["[[<source-a>]]", "[[<source-b>]]"]   # collected from the cited wiki pages
aliases: []
---
```

Body: the answer from step 4, lightly reshaped into a normal page (Definition / Why it matters / Mechanics or sub-sections / Related / Open questions). Preserve all `[[wikilinks]]`.

Update `wiki/MOC.md`: add the new page under an "Inbox / drafts" section (create the section if it doesn't exist). The user moves it to its real home later.

Report the path of the promoted page.

## Suggested-ingests footer

If the answer had to drop claims for lack of citation, surface that with a footer **before** the promotion offer:

```
Suggested ingests to fill gaps:
- A source on <topic> — try the canonical paper or a high-quality article.
```

## Constraints

- **Never read from `raw/`.** Not even to "double-check" something. The wiki is the truth surface for queries; if the wiki is wrong, fix it via `/ingest` of a better source or a hand edit, not by going around it.
- **Never invent citations.** Every `[[slug]]` in the answer must point to a real wiki page that actually contains the cited claim.
- **No raw source quotes in the answer.** Paraphrase from wiki pages only.
- Cap the working set at ~15 pages. If the question pulls more, ask the user to narrow it.
- **Never auto-promote.** Promotion only happens after explicit user confirmation in a follow-up turn.

# Hardening lessons — the disciplines that keep a wiki from rotting

*Hackable seam: this is the discipline set baked into the generated commands and
conventions doc. Edit it to change what the scaffolded wiki enforces. Each discipline
below maps to a rule in `WIKI-CONVENTIONS.md.template` and/or the three commands.*

The bare LLM-wiki pattern degrades at scale. These are the disciplines — drawn from
real use of the pattern and the common critiques of it — that the scaffold ships so it
doesn't. Treat them as load-bearing; the SKILL.md "hard nevers" enforce them.

## 1. Cite or stay silent

Every non-trivial claim on a wiki page traces to at least one `[[source]]`. If a claim
can't be cited, it doesn't get written — the command says so and names a source to
ingest. *Why:* the wiki's value is that you can trust it without re-reading raw docs;
uncited synthesis is just confident guessing, and it's the first thing to mislead you
when you reach Intent.

→ Enforced in: `ingest.md` (Step 6 frontmatter `sources:`), `query.md` (never invent a
citation), conventions hard-rule #2.

## 2. `/query` reads `wiki/` only — never `raw/`

A query never falls back to reading the raw sources. If the wiki can't answer, the
answer is "ingest more," not "let me go read the docs." *Why:* the moment query reads
raw, you're back to RAG and the synthesis layer is dead weight. Keeping query on `wiki/`
only is what *forces* the wiki to actually capture knowledge.

→ Enforced in: `query.md` (critical rule + constraints), conventions hard-rule #3.

## 3. Plan before you write; everything reversible

`/ingest` proposes a concrete change plan and waits for approval. `--yolo` skips the
approval for fast solo runs — but the wiki being **its own git repo** means even a
`--yolo` ingest is fully reversible (diff, revert). *Why:* the right level of automation
is "everything *reversibly*," not "everything always." Early rebuilds of the pattern
corrupted vaults by auto-writing model slop (XML thinking tags saved verbatim,
stringified dicts in frontmatter). Plan-pass + git is the cheap guard.

→ Enforced in: `ingest.md` (Step 5 plan-pass), `wiki-init` Step 4 (git init), keep
`--yolo` available.

## 4. Rewrite, don't just append

When a new source supersedes a claim, the page is **rewritten** to reflect current
understanding, and the old version is preserved as a dated note below — not left to sit
unmarked next to the new claim. *Why:* the #1 failure mode of the append-only version is
that old beliefs never update; future-you (and `/query`) sees two contradictory claims
with no signal which is current. A thesis that was "speculation" should visibly become
"confirmed."

→ Enforced in: `ingest.md` (Step 4 reconcile + Step 6 existing-page updates), conventions
hard-rule #5.

## 5. Lint is the garbage collector — safe-fix-only

`/lint` periodically surfaces broken links, orphans, stale claims, contradictions,
frontmatter drift, and suggested pages. Only **mechanical** categories auto-fix under
`--fix` (broken-link near-miss renames, frontmatter normalization, trivial reciprocal
backlinks). Contradictions, stale claims, merges, and new-page creation are **surfaced
for review, never auto-applied.** *Why:* "vaults rot in silence." A periodic audit is
what catches the rot; but resolving a contradiction or folding a duplicate needs
judgment, so the lint proposes and the human disposes.

→ Enforced in: `lint.md` (Step 2 checks, Step 4 safe-fix allowlist).

## 6. Three layers, one rule each

`raw/` is immutable (never edited except `/ingest` saving a URL fetch). `wiki/` is
synthesized + cross-linked. `_meta/` is the log + reports. *Why:* the layering is what
makes citations traceable (wiki claim → `[[source]]` page → `raw/` file) and what lets
`/query` trust `wiki/` as the truth surface.

→ Enforced in: conventions structure table + hard-rule #1.

## 7. Human-first formatting (the deliberate divergence)

Pages are written to be read by the human and browsed in Obsidian — **not** optimized
for agent retrieval with machine-first preambles. *Why:* this wiki is the Understanding
phase; its purpose is your mental model. The agent-first store is the separate project
Expert. See `llm-wiki-pattern.md` for the full argument.

→ Enforced in: conventions page-body shape (human prose), `wiki-init` P2.

## Deferred (don't build into the three commands without an explicit ask)

Scheduled/automatic maintenance agents (nightly close-out, weekly reconciliation) are a
real enhancement of the pattern — but they're **out of scope** here. The harness has
`/loop` and `/schedule` that *could* later tick `/lint`, but that's a future iteration,
not part of `wiki-init`. Also deferred: slides/charts/search-UI/synthetic-data/publishing.
Note these in the conventions doc's v2 list so a future session doesn't drift into them.

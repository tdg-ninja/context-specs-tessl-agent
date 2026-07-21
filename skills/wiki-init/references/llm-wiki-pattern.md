# The LLM Wiki pattern — provenance, and what we kept vs. changed

*Hackable seam: this is where the idea's framing and the kept-vs-changed list live.
Edit it to re-tune how `wiki-init` explains itself.*

## Credit

The shape is **Andrej Karpathy's "LLM Wiki."** Credit it **by name** when you explain
the skill. Do **not** embed the gist URL in the generated wiki or in the skill — name
the idea, not the link.

## The core idea (say this in plain language)

Two ways to use an LLM over a pile of documents:

- **RAG (retrieve-augment-generate):** at *query* time, retrieve chunks of raw docs and
  stuff them into context. The connection between sources is re-derived on every single
  question, and it's only as good as that one retrieval.
- **LLM Wiki:** do the synthesis **once, at ingest time.** When a source lands, the LLM
  reads it, extracts the entities/concepts/claims, and *integrates* them into a persistent
  set of cross-linked markdown pages — creating new pages and revising existing ones. The
  cross-references are already there. Questions are answered from the synthesized wiki,
  not the raw pile.

The wiki is a **persistent, compounding artifact.** Every source added makes it richer.

## Why it works (the bookkeeping insight)

The reason humans abandon wikis and second-brains isn't the reading or the thinking —
it's the *bookkeeping*: updating cross-references across many files, keeping the index
current, reconciling a new note against old ones. That clerical maintenance is exactly
what an LLM is good at and tireless about. So the division of labor is:

- **Human:** curate which sources go in, direct the analysis, ask the questions, decide
  what matters.
- **LLM:** do all the maintenance and bookkeeping — synthesis, cross-linking, index
  upkeep, health checks.

## What we kept from the bare pattern

- **Three layers:** immutable `raw/` sources → synthesized `wiki/` → `_meta/` (log +
  reports). Plus an index (`MOC.md`) and an append-only ingest log.
- **The three operations:** `ingest` (synthesize a new source in), `query` (answer from
  the wiki, optionally file the answer back as a page), `lint` (periodic audit for
  contradictions, stale claims, orphans, missing links).
- **Synthesis-at-ingest, not at query.** The load-bearing distinction from RAG.

## What we changed / hardened (and why)

The bare pattern is "a doc + instructions." Run at scale it rots — the common critique is
that past ~100 sources, stale claims go invisible, contradictions pile up faster than
anyone resolves them, and the link graph becomes unnavigable. The disciplines we ship to
prevent that live in `hardening-lessons.md`; in brief:

- **Cite or stay silent** — every wiki claim traces to a `[[source]]`. (Trust.)
- **Plan-before-write with `--yolo`** + the wiki being its own git repo — reversibility,
  not blind automation.
- **`/query` reads `wiki/` only, never `raw/`** — preserves the whole synthesis contract.
- **Rewrite, don't just append** — superseded claims get updated, old version kept as a
  dated note, so current and stale don't sit unmarked side by side.
- **Lint is safe-fix-only** — it surfaces contradictions/stale/orphans; only mechanical
  categories auto-fix.

## The one place we deliberately diverge: human-first, not AI-first

A well-known rebuild of the pattern argues for an **"AI-first vault"** — optimize every
note for LLM retrieval (a "For future Claude" preamble, machine-first formatting),
because "you don't read your own notes, the LLM does."

**We reject that here, on purpose.** In this harness the wiki *is* the Understanding
phase — its entire job is to build the *human's* mental model so they can express sharper
Intent. The audience is the human; pages stay human-readable and Obsidian-browsable. The
agent-first knowledge store already exists and is a *different* artifact: the project
**Expert** (`.claude/skills/expert/`), which is per-project code memory written by
`/learn`. Keep the two distinct:

> **wiki = cross-project domain + architecture knowledge, for the human.**
> **Expert = per-project code memory, for the agent.**

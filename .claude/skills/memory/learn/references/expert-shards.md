# Expert shard taxonomy

**Hackable seam.** A project may add, rename, or split shards. These are the
defaults. The Expert is the project's *lazy* memory — pulled on demand by `/intent`,
`/spec-planning`, `/spec-validate`, and `/implement-*` via the catalog, or read
directly. It is shaped exactly like a framework expert (so it composes with them):

```
.claude/skills/expert/
├── SKILL.md               # Expert Mode entry: quick-reference table → references/
├── references/
│   ├── architecture.md    # Decisions, layering, boundaries, the "why" of the shape
│   ├── verification.md    # How features get tested/verified in THIS project
│   ├── patterns.md        # Soft DO/DON'T, with examples (taste, judgment)
│   ├── procedural.md      # "How to add a new feature here" — the steps
│   ├── core-files.md      # Key files & abstractions, with paths
│   ├── invariants.md      # HARD rules the codebase upholds (see below)
│   ├── lessons.md         # Episodic negative memory (see below)
│   └── changelog.md       # Provenance: what /learn changed, when, why, vote
└── scripts/
    └── (optional signal scripts, like any expert)
```

## The two shards this design adds

### invariants.md — hard rules (distinct from patterns.md)
`patterns.md` is *soft* ("prefer composition here"); `invariants.md` is *hard*
("Repo layer never imports Service"). The distinguishing test: **can it be
mechanically checked?** If yes, it's an invariant and the highest-value ones become
lints (see `invariant-discovery.md`). If it needs judgment, it's a pattern.

Each invariant entry: the rule, *why* it holds, and — once promoted — a pointer to
its lint (`scripts/lints/<name>.sh`).

### lessons.md — episodic negative memory
"X failed because Y — don't reach for X here." Appended by `/capture-lesson` (Path
B) from real struggles; curated by `/learn` (Path A). Every entry is **dated**,
**attributed** (which feature/sha, what tripped), and framed as a **reason, not a
prohibition** (so a future agent can re-evaluate whether Y still holds). See
`lessons-curation.md`.

## SKILL.md shape
Mirror the framework-expert shape (`expert-sdd-creator`'s `expert-structure.md`): a
short Expert-Mode entry with a quick-reference table mapping topics → reference
files. The body stays small; the references hold the density. Front-matter
`description` ends with `(project)` and lists triggers so the catalog can activate
it during the SDD phases.

## Bootstrap / --rebuild
On a fresh project (no Expert) or `--rebuild`, seed every shard by scanning
committed code: derive `core-files.md` from the actual tree, `verification.md` from
the test/CI setup, `architecture.md` from the module layering, `invariants.md` from
rules the code visibly upholds (conservatively — see `invariant-discovery.md`).
Leave `lessons.md` empty if there's nothing to say; never invent failures.

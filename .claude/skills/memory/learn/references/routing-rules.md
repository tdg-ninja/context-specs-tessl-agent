# Routing rules — the four destinations

**Hackable seam.** This file *is* the judicial bar. A project edits the predicates
and the caps to its taste; the flow doesn't change.

Every fact worth remembering routes to **exactly one** destination. Most facts go
to the last two rows.

| Destination | Use when | Cost model |
|---|---|---|
| **A lint** (`scripts/lints/*` → `local-checks.sh`) | The rule is *mechanically checkable* — pass/fail needs no judgment (layer-dependency direction, "parse at boundaries", naming, no raw SQL interpolation, structured-logging-only, file-size caps) | Best: enforced on every PR forever, and the failure message doubles as a fix prompt. See `invariant-discovery.md`. |
| **Eager prose** (`AGENTS.md`) | It clears **all five predicates** below | Paid in tokens on *every* session that touches the folder — strict bar. |
| **Lazy prose** (an Expert shard) | Useful when an agent is *deliberately reasoning* about this area, but not needed pre-emptively | Paid only when consulted — looser bar. The default home for real knowledge. |
| **Nowhere** | Inferable from the code, taste-only, or transient | — |

## The five-predicate test for *eager* (AGENTS.md) placement

A fact earns a line in AGENTS.md only if **all five** hold. If any fails, it goes
to the Expert (lazy) or nowhere.

1. **Needed before consultation** — an agent will hit the relevant code *before it
   would think to open the Expert*. (Pre-emptive, not on-demand.)
2. **Non-inferable** — it can't be read off the local code; it's tribal/contextual.
3. **Harm on violation** — breaking it breaks behavior, leaks data, or regresses.
   Not style, not taste.
4. **Stable** — it won't rot next week.
5. **Local (or truly global)** — for a nested AGENTS.md, the rule is specific to
   that folder; for the root, it's genuinely repo-wide.

## Why the bar differs

The Expert is *pulled on demand* — progressive disclosure. AGENTS.md is *eager* —
the agent reads it automatically as it enters a folder, before knowing if it's
relevant. So every AGENTS.md line is a standing tax; every Expert line is paid only
when it earns its keep. **When in doubt, prefer the Expert over AGENTS.md, and
prefer nothing over noise.**

## Line-count caps (tweakable)

- Root `AGENTS.md`: **≤ 150 lines.** Beyond ~150, research shows diminishing
  returns and rising inference cost with no quality gain.
- Nested `AGENTS.md`: **≤ 80 lines.**
- `scripts/check-agents-md.sh` enforces these mechanically.

## The map/territory rule

AGENTS.md **points into** the Expert; it never copies it. A pointer ("this folder
does X; consult `expert/references/Y.md` before non-trivial work") stays correct as
the Expert grows. A copied paragraph drifts. Reference, don't duplicate.

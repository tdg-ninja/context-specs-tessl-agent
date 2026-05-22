# Consensus

**Hackable seam.** The voting threshold that gates a memory write. Mirrors the
multi-agent consensus `/spec-validate` already uses, so the project has one mental
model for "a panel decided," not two.

## Why consensus here
Memory is long-lived and compounding. A wrong write poisons every future session
that reads it. The trade is cheap: a few extra LLM calls per merge in exchange for
not corrupting long-term memory on every commit. Most merges (vuln fixes, refactors
that don't change shape, routine bug fixes) produce **no change** — 0/3 across all
surfaces is the common, correct outcome.

## How to run it
1. Spawn **2–3** parallel reviewers (cheap model is fine — this is judgment over a
   bounded diff, not generation).
2. Give each: the merged diff, the current Expert shards, the touched AGENTS.md
   files, and the PRD/spec for the *why*.
3. Each votes **per surface** (shards / invariants / lessons / AGENTS.md): does
   anything need to change, and if so what?
4. Apply only changes that meet the **threshold (default 2/3)**. Discard 1/3.

## Tuning
- Raise to **3/3** for a stricter bar (fewer, higher-confidence writes).
- Lower to a single reviewer only for low-stakes projects that want speed over
  precision — not recommended for invariant/lint promotion, which should stay
  consensus-gated *and* human-confirmed.

## Drift signal
If consensus returns 0/3 for *many* consecutive merges, that's worth noticing: the
Expert may be too coarse to capture what's changing, or the project is genuinely
stable. Either way, it's an observability signal, not a bug — surface it, don't
force a write.

# The eval contract

This is the discipline behind Step 5's first outcome. An eval is the load-bearing artifact
of the whole skill: it freezes *"given this context, the skill should behave like this"* so
a future context change can't silently regress it. It is the harness's version of the
Chase/LangSmith flywheel — *observe a trace → capture it as an eval → fix the context → it
persists as a regression test.*

> Governing principle: **an eval tests the harness's own skills/context, not the product.**
> A PRD runner (`prds/<f>/run-prd-test.sh`) asks "does the *feature* work?". An eval asks
> "given this context, does the *skill* behave as it should?". Different question, different
> home — keep them separate so neither rots the other.

**Why this is exciting (tell the human).** Authoring an eval is the moment the human's *own
project* becomes an agent harness they can evaluate and improve: each eval is a graded trial of
the project's context that compounds — the project gets better at building itself over time.
That framing is worth saying out loud as you capture one.

## Where evals live — in the project being evaluated, not here

Evals live in the **dev's project** (the repo whose PR you're evaluating), under `evals/` at
that repo root. They are a *runtime artifact of the project*, like `prds/` and `specs/` — they
do **not** live in the context-specs skill library. One directory per case:

```
<project-repo>/evals/
├── README.md                       # the contract, for humans who find the dir cold
├── <name>/
│   ├── fixture/                     # the context the agent had (or a pointer to it)
│   ├── judge.md                     # the rubric: what behavior is expected, and why
│   └── run-eval.sh                  # exits 0 iff the expected behavior holds
└── run-all.sh                       # optional aggregator: run every <name>/run-eval.sh
```

`<name>` is a short kebab slug describing the behavior under test — e.g.
`spec-planning-honors-ssr-constraint`, not `feature-search`. The name is about the *skill
behavior*, because that's what regresses.

### Scaffolding `evals/` on first use

If the project has no `evals/` dir yet, create it when you author the first eval — drop in a
`README.md` (so the next person who finds the dir cold understands the contract) and an optional
`run-all.sh` aggregator. These commit on the same branch as the eval (see `outcomes.md`).

`evals/README.md` (project-facing — adapt the wording):

```markdown
# `evals/` — regression tests over this project's harness skills/context

Authored by `/evaluate-sessions` when a build trail reveals a skill behaving well or badly
because of this project's context (an Expert shard, an AGENTS.md pointer, a skill's text, a
spec). Evals test the **harness** ("given this context, does the skill behave?"); `prds/<f>/
run-prd-test.sh` tests the **product** ("does the feature work?"). Keep them separate.

Contract: one dir per case — `evals/<name>/{fixture/, judge.md, run-eval.sh}`. `run-eval.sh`
exits 0 iff the expected behavior holds (deterministic checks, a `claude -p` judge, or a mix).
A new eval must go RED against the context that misled the agent and GREEN once it's fixed.
```

`evals/run-all.sh` (optional aggregator):

```bash
#!/usr/bin/env bash
# Run every evals/<name>/run-eval.sh. Exit 0 iff all pass.
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
fail=0 ran=0
for runner in "$here"/*/run-eval.sh; do
  [[ -e "$runner" ]] || continue
  ran=$((ran + 1)); name="$(basename "$(dirname "$runner")")"
  if bash "$runner"; then echo "PASS  $name"; else echo "FAIL  $name"; fail=1; fi
done
(( ran == 0 )) && echo "no evals yet (evals/<name>/run-eval.sh)"
exit $fail
```

## The runner contract (mirrors the PRD runner deliberately)

`evals/<name>/run-eval.sh` is the single contract, and it borrows
`prds/<f>/run-prd-test.sh`'s shape exactly so the project has *one* mental model for
"runnable definition of correct":

- **Exit 0 = the expected behavior holds; non-zero = it doesn't.** That's the whole API.
- **Internals are free.** A deterministic grep over a produced artifact, a `claude -p`
  LLM-as-judge against `judge.md`'s rubric, or a mix. The harness contracts only on the
  exit code.
- **Self-contained under `evals/<name>/`.** Fixtures, judge prompt, helper files all live
  beside the runner, sandboxed from the project's own test discovery (same reason PRD
  runners live under `prds/`).

### The LLM-as-judge shape

Most context evals are judgments, not deterministic checks — so the common body is:

```bash
#!/usr/bin/env bash
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"

# Reproduce the decision point: give the skill the SAME context the trace showed it had,
# then judge the output against the rubric. Keep it cheap (Haiku is usually enough).
verdict="$(claude -p --model claude-haiku-4-5 \
  "$(cat "$here/judge.md")

  ===== ARTIFACT UNDER TEST =====
  $(cat "$here/fixture/produced-spec.md")

  Answer with a single line: PASS or FAIL: <one-line reason>.")"

echo "$verdict"
grep -q '^PASS' <<<"$verdict"
```

`judge.md` states the expected behavior and the *why* in plain language — it is the rubric,
and it is a hackable seam the project tunes. Keep judges narrow: one behavior per eval, so a
FAIL points at one thing.

## The right-reason check (inverse of `/intent`'s)

This is what separates a real eval from a fake one. `/intent` requires a PRD runner to
**fail for the right reason** before the feature exists. An eval is the mirror:

1. **It must FAIL against the context that misled the agent.** Run `run-eval.sh` *before*
   you apply the context fix — it has to go red, exercising the actual defect the trace
   showed. An eval that passes trivially proves nothing and is worse than no eval (it reads
   as "covered" while covering nothing).
2. **It must PASS once the context fix is in.** After you fix the Expert/AGENTS.md/skill,
   re-run — it goes green. Red-before, green-after is the proof the eval and the fix are
   about the same thing.

If you can't get an eval to go red against the defect, you haven't understood the defect
yet — go back to the trace. (This mirrors `/learn`'s rule that a drafted lint must pass
against the merged code before inclusion: an assertion that can't tell right from wrong is
not an assertion.)

## When NOT to write an eval

- The finding was **inherent difficulty**, not a context defect (S4) — nothing to freeze.
- The behavior is already covered by an existing eval — extend `judge.md` instead of
  spawning a near-duplicate.
- The fix is a **lint** (mechanically checkable). Then the lint *is* the regression test —
  route it as a lint (the first destination in SKILL.md's S9), don't also write an eval.

A clean trail, or a trail whose only finding is "this was hard," produces **no eval**. That
is a correct and common outcome.

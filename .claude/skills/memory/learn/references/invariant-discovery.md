# Invariant discovery & promotion to lints

**Hackable seam.** How `/learn` surfaces the project's architectural invariants and
turns the best of them into mechanical checks — without overfitting.

## What a custom lint is

A lint is a program that reads the source and exits non-zero on a violation. A
*custom* lint is one you write — and the simplest, most language-agnostic flavor is
a short script in `scripts/lints/` wired into `scripts/local-checks.sh`. No linter
framework required: glob files, inspect their contents (grep or a parser), assert a
structural fact, exit 1 with a remediation message.

Two properties make custom lints the highest-value memory destination:

1. **The error message is a prompt.** Don't just say "violation" — say how to fix
   it. The failing lint feeds remediation straight into the agent's context, so it
   self-corrects with no human. A prose rule in AGENTS.md is advice the agent
   *might* follow; a lint is a rule it *cannot ship past*, plus the fix.
2. **It scales the way agents scale.** Once encoded, it applies to every file and
   every future PR at once.

## Examples of lint-able invariants

- **Layer dependency direction** — "files under `repo/` may not import from
  `service/`." Walk imports; fail on a forward-violating edge.
  ```bash
  if grep -rEl "from ['\"].*/service/" src/repo/ ; then
    echo "❌ repo/ must not import from service/ (layer direction Types→Repo→Service→UI).
       Move the shared type to types/, or invert via a Provider interface." >&2
    exit 1
  fi
  ```
- **No raw SQL string interpolation** (injection class) — grep for interpolated SQL.
- **Structured logging only** — no `console.log(`/`print(` in `src/`.
- **Naming/format** — migration filenames match `^\d{14}_`.
- **File-size cap / public-API drift** — `wc -l` ceiling; exports match `openapi.yaml`.
- **Memory freshness** — `check-agents-md.sh` itself (referenced paths exist).

## What stays prose (NOT a lint)
Anything needing judgment: "is this the right abstraction?", "prefer composition
here." Those are `patterns.md` (Expert), or — if pre-emptively load-bearing —
AGENTS.md. The test: **if pass/fail is unambiguous, lint it; if it needs taste, it
stays prose.**

## The discipline (avoid overfitting)

A discovered "invariant" can be an incidental pattern, or a quirk of the current
model's failures rather than a real codebase property. So:

1. **Consensus-gate it** like every `/learn` write.
2. **Prose first, lint on recurrence.** First sighting → record in `invariants.md`
   and flag a candidate lint. Same invariant seen across merges → promote to an
   enforced lint. One occurrence is a pattern; repetition is an invariant.
3. **Frame the *reason*.** "Repo→Service imports break the build because layers are
   compiled bottom-up" survives model upgrades; a bare prohibition doesn't.
4. **The drafted lint MUST pass current main.** Run it against the just-merged code
   before including it. If it reddens the merge it was born from, it's wrong — fix
   or drop it. (This is `/intent`'s right-reason check, inverted: it must *pass*.)
5. **Human disposes.** The candidate lands in the `learn/<sha>` PR; the human
   confirms before it becomes a blocking gate. Discovery proposes; the merge blesses.

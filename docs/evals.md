# Tessl evals

This repo keeps a small Tessl eval suite for high-value Context Specs and Dark Factory behavior contracts. Evals complement `tessl review run quality`; they do not replace skill quality review or deterministic checks.

## Current scenarios

- **`dark-factory-malformed-issue-rejection`** — malformed Dark Factory issues are rejected before implementation, with a diagnosis-first report and no repo edits.
- **`dark-factory-no-publish-from-issues`** — issue-originated Dark Factory work may make safe repo changes and open a PR, but does not publish Tessl registry versions.
- **`context-specs-install-and-skill-invariants`** — install docs distinguish registry install from the compatibility CLI, `spec-planning` stays compact, and `implement-mainspec` preserves sequential versus parallel mode guidance.

## Scenario shape

Each scenario lives under `evals/<scenario-name>/` and contains:

- **`task.md`** — the task prompt the eval agent sees.
- **`criteria.json`** — a weighted checklist rubric with `context`, `type: "weighted_checklist"`, and `checklist` items containing `name`, `description`, and `max_score`.
- **`scenario.json`** — optional metadata, fixtures, includes, or setup declarations.

Validate the checked-in shape before running remote evals:

```bash
tessl eval lint .
```

## Running evals

Run the suite manually when changing Dark Factory issue dispatch, install docs, or the covered skill entrypoints:

```bash
tessl eval run . --label "context-specs critical workflows"
```

Use a scoped run for initial validation or when iterating on a single skill:

```bash
tessl eval run . --skill spec-planning --label "spec-planning invariant check"
tessl eval run . --skill implement-mainspec --label "implement-mainspec mode guidance"
```

For a routing-only activation pass, skip forced activation and scoring:

```bash
tessl eval run . --skip-forced-context-activation --skip-scoring --label "context-specs activation check"
```

## Cost and cadence

- Keep the suite small and high-signal.
- Prefer `workflow_dispatch` for CI runs until the eval signal is proven useful.
- Do not run these evals on every PR synchronize event by default.
- Use `tessl eval lint .` as the cheap deterministic preflight.
- Continue running `tessl review run quality` for skill/plugin quality gates.

## Interpreting results

After a run starts, use the run URL or:

```bash
tessl eval list --mine --limit 5
tessl eval view <run-id>
```

Treat failures as harness feedback. Fix the relevant docs, skills, Dark Factory prompts, or scenario criteria, then rerun only the smallest useful scope.

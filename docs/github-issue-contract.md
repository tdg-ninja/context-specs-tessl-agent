# GitHub issue contract for Dark Factory

Dark Factory issue dispatch expects a GitHub issue to be a clear work order. The
Tessl agent validates this structure before it edits files.

## Required sections

Use these headings in the issue body:

```md
## Goal

What should change, and why?

## Scope

Files, directories, workflows, docs, or systems likely involved. Include what is
out of scope when the boundary matters.

## Acceptance criteria

- [ ] Observable outcome or behavior.
- [ ] Checks, docs, PR shape, or verification expected when done.

## Constraints

What the agent must not do, release boundaries, compatibility requirements,
security concerns, or unknowns that require diagnosis instead of implementation.
```

## Optional sections

```md
## What is Tessl here?

Name any Tessl surfaces this work should touch, such as `tessl agent`, `tessl
review run quality`, `tessl plugin lint`, `tessl plugin publish`, `tessl install`,
or `context-specs verify`.

## Evidence

Links, screenshots, command output paths, failing logs, or examples.
```

## Dispatch labels

- **`dark-factory`** — dispatches the issue to the Tessl agent workflow.
- **`tessl-registry`** — work touches plugin packaging, review, publishing, or registry installability.
- **`consumer-rollout`** — work updates another repository to a Context Specs version.
- **`maintenance`** — cleanup, docs, refactors, or recurring harness upkeep.

## Validation behavior

Before implementation, the agent checks that the issue has:

- a non-empty title;
- `## Goal` with concrete intent;
- `## Scope` with touched areas or an explicit discovery scope;
- `## Acceptance criteria` with at least one checkbox or bullet;
- `## Constraints` with boundaries, or an explicit statement that there are none;
- the `dark-factory` label, unless manually dispatched or triggered by `/dark-factory`.

If the issue is missing required structure, the agent writes a diagnosis report,
comments on the issue with the missing fields, and does not edit repo files.

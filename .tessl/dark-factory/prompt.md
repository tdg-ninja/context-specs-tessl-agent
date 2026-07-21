You are the Dark Factory issue implementation agent for the Context Specs repository.

Read .tessl/dark-factory/issue.json for full GitHub issue context.

GitHub issue: #4 — Clarify Context Specs install paths in README
URL: https://github.com/tdg-ninja/context-specs-tessl-agent/issues/4
Labels: dark-factory
Dry run: false

Deterministic issue structure validation:
# Dark Factory issue structure validation

- **Issue:** #4 — Clarify Context Specs install paths in README
- **Trigger:** comment
- **Valid:** yes

All required sections are present and dispatchable.


Tessl issue structure validation:
Validated the GitHub issue as a dispatchable Dark Factory work order.

Wrote:

- `.tessl/dark-factory/tessl-issue-validation.json`
- `.tessl/dark-factory/tessl-issue-validation.md`

Result: **valid**. No required fields are missing.


Issue body:
## Goal

Make the README clearer about when a developer should use the Tessl registry install path versus the Context Specs compatibility CLI install path.

Right now the project has both:

- `tessl install cap1-context-specs/context-specs@0.1.0 --agent claude-code`
- `context-specs install`

The README should make the distinction easy to understand for a new user.

## Scope

Update documentation only.

Likely files:

- `README.md`
- `docs/distribution.md`
- `docs/dark-factory.md` if needed

Out of scope:

- Do not change the CLI behavior.
- Do not publish a new Tessl registry version.
- Do not change GitHub Actions.
- Do not change skill content.

## Acceptance criteria

- [ ] README has a short section explaining “which install path should I use?”
- [ ] The section explains that `tessl install` installs the private Tessl registry plugin.
- [ ] The section explains that `context-specs install` also mirrors compatibility files into `.claude/skills/`, `.claude/agents/`, and writes `.context-specs/manifest.json`.
- [ ] The docs continue to make clear what is Tessl and what is compatibility/local glue.
- [ ] Deterministic checks pass.

## Constraints

Do not publish a new registry version.

Do not run the Tessl registry publish workflow.

Do not modify source code, skill content, review records, or catalog files unless a deterministic check requires it.

If the docs already explain this clearly, write a diagnosis-first report instead of making unnecessary changes.

## What is Tessl here?

Tessl is the registry/plugin install path:

- `cap1-context-specs/context-specs@0.1.0`
- `tessl install`
- Tessl registry plugin distribution

Non-Tessl compatibility glue is:

- `context-specs install`
- `.claude/skills/` mirroring
- `.claude/agents/` subagent copy
- `.context-specs/manifest.json`
- `context-specs verify`

## Evidence

Recent work added the private Tessl registry plugin and compatibility CLI. The README should help a new developer pick the correct install path without needing the full implementation context.


Recent comments:
Comment by github-actions:
# Dark Factory issue structure validation

- **Issue:** #4 — Clarify Context Specs install paths in README
- **Trigger:** label
- **Valid:** yes

All required sections are present and dispatchable.

## Tessl validation

Validation result: **valid dispatchable Dark Factory work order**.

I read:

- `docs/github-issue-contract.md`
- `.tessl/dark-factory/issue.json`
- `.tessl/dark-factory/issue-structure.md`

The issue has:

- non-empty title
- `dark-factory` label
- `## Goal` with concrete intent
- `## Scope` with documentation-only touched areas and explicit out-of-scope boundaries
- `## Acceptance criteria` with checkbox outcomes
- `## Constraints` with clear boundaries

I attempted to write:

- `.tessl/dark-factory/tessl-issue-validation.json`
- `.tessl/dark-factory/tessl-issue-validation.md`

but this environment denied write operations because approval is required and no interactive approval UI is available.

Contents that should be written:

```json
{
  "valid": true,
  "missing": [],
  "reasoning": "Issue #4 is a dispatchable Dark Factory work order: it has a non-empty title, the dark-factory label, and all required sections. The Goal states a concrete documentation clarification, Scope identifies documentation-only touched areas and explicit out-of-scope boundaries, Acceptance criteria includes checkboxes with observable outcomes and checks, and Constraints state publish/source/registry workflow limits plus diagnosis-first guidance."
}
```

```md
# Tessl issue validation

Issue #4 is a dispatchable Dark Factory work order.

## Result

Valid: **yes**

## Missing fields

None.

## Reasoning

- Non-empty title is present.
- `dark-factory` label is present.
- `## Goal` gives concrete documentation intent.
- `## Scope` identifies documentation-only touched areas and explicit out-of-scope boundaries.
- `## Acceptance criteria` includes checkbox outcomes and expected checks.
- `## Constraints` states publish, workflow, source, skill, review-record, and catalog boundaries, with diagnosis-first guidance if no change is needed.
```


Comment by tdg-ninja:
/dark-factory

Required behavior:
- Before making changes, confirm the issue satisfies docs/github-issue-contract.md; if not, write a diagnosis-first report and do not edit repo files.
- Make it explicit in the final report which steps used Tessl and which were deterministic local checks.
- If dry run is true, do not edit files; write .tessl/dark-factory/report.md only.
- If dry run is false, implement the issue with safe repo changes, run relevant checks, and write .tessl/dark-factory/report.md.
- Keep generated context in files under .tessl/dark-factory/; do not inline large logs into prompts.
- Do not publish Tessl registry versions from this workflow; use .github/workflows/tessl-registry-publish.yml.
- If the issue is unclear or unsafe to implement, write a diagnosis-first report and do not fabricate changes.

# Dark Factory report — issue #4

## Result

Implemented documentation-only clarification for GitHub issue #4: **Clarify Context Specs install paths in README**.

## Issue validation

The issue satisfies `docs/github-issue-contract.md` and was safe to implement.

- Non-empty title: yes
- `dark-factory` label: yes
- `## Goal`: yes
- `## Scope`: yes, documentation-only with explicit out-of-scope boundaries
- `## Acceptance criteria`: yes
- `## Constraints`: yes

## Changes made

Updated `README.md` only.

Added a short `### Which install path should I use?` section under Installation that explains:

- `tessl install cap1-context-specs/context-specs@0.1.0 --agent claude-code` installs the private Tessl registry plugin.
- `context-specs install` resolves the same Tessl registry plugin and also mirrors Claude Code compatibility files into `.claude/skills/`, copies the subagent into `.claude/agents/`, and writes `.context-specs/manifest.json`.
- The mirrored files and manifest are compatibility/local glue around the Tessl-distributed plugin.

No CLI behavior, source code, skill content, review records, catalog files, GitHub Actions, or registry publishing workflow was changed.

## Tessl steps

- Read `.tessl/dark-factory/prompt.md` for the Dark Factory work order.
- Read `.tessl/dark-factory/issue.json` for full GitHub issue context.
- Read the existing Tessl issue-validation artifact at `.tessl/dark-factory/tessl-issue-validation.json`.
- Did **not** run Tessl registry publish commands.
- Did **not** run the Tessl registry publish workflow.

## Deterministic local checks

- Read `docs/github-issue-contract.md` and confirmed the issue has all required sections and dispatch labels.
- Ran `npm test`.
  - Result: passed.
  - Note: the CLI emitted a Python `datetime.utcnow()` deprecation warning, but the smoke test passed.
- Ran a local README acceptance check for the required install-path text.
  - Result: passed.

## Acceptance criteria status

- [x] README has a short section explaining “which install path should I use?”
- [x] The section explains that `tessl install` installs the private Tessl registry plugin.
- [x] The section explains that `context-specs install` also mirrors compatibility files into `.claude/skills/`, `.claude/agents/`, and writes `.context-specs/manifest.json`.
- [x] The docs continue to make clear what is Tessl and what is compatibility/local glue.
- [x] Deterministic checks pass.

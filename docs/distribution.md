# Distribution and review model

Context Specs is distributed as a reviewed catalog of skills and subagents plus a
small CLI.

## Developer workflow

- Run `context-specs install` in a project to copy reviewed skills to
  `.claude/skills/` and subagents to `.claude/agents/`.
- Commit `.context-specs/manifest.json` in the target project to pin the source,
  catalog digest, artifact digests, and review status.
- Run `context-specs update` to refresh to a newer catalog.
- Run `context-specs verify` in CI to detect local edits, missing files, or an
  unreviewed install.

## Maintainer workflow

- Edit skills, reference docs, scripts, or subagents in this repository.
- Review each changed installable artifact before distribution.
- Write or update the matching file under `catalog/reviews/` with the artifact
  path, SHA-256 digest, status, reviewer, timestamp, and notes.
- Run `context-specs catalog generate --source .`.
- Commit the changed source, review records, and `catalog/skills-manifest.json`
  together.

## Trust boundary

- A skill is installable by default only when its current `SKILL.md` digest matches
  a `catalog/reviews/*.json` record with `status: reviewed`.
- A subagent is installable by default only when its current file digest has the
  same reviewed status.
- The generated catalog also records every file inside each skill directory so the
  CLI can verify references and scripts were not changed after catalog generation.
- `--allow-unreviewed` bypasses the review gate for local development only.

## Versioning

- Pin a git tag or branch with `--ref` when installing from a git source.
- The target project's `.context-specs/manifest.json` records the catalog digest
  and source revision used for that install.
- Re-running `context-specs update --ref <tag>` moves a project to an explicit
  reviewed release.

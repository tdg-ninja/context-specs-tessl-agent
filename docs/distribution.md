# Distribution and review model

Context Specs is distributed as the private Tessl registry plugin
`cap1-context-specs/context-specs` plus a small compatibility CLI.

## Developer workflow

- Run `tessl install cap1-context-specs/context-specs@0.1.0 --agent claude-code` to install the registry plugin.
- Run `context-specs install` when the target repo also needs `.claude/skills/`, `.claude/agents/`, and `.context-specs/manifest.json` compatibility files.
- Commit `.context-specs/manifest.json` in the target project to pin the registry plugin, artifact digests, and review authority.
- Run `context-specs update` to refresh to a newer registry version.
- Run `context-specs verify` in CI to detect local edits or missing compatibility files.

## Maintainer workflow

- Edit skills, reference docs, scripts, or subagents in this repository.
- Review each changed skill with `tessl review run quality` in the `cap1-context-specs` workspace.
- Write or update the matching file under `catalog/reviews/` with the artifact path, SHA-256 digest, review run ID, score, status, reviewer, timestamp, and notes.
- Run `context-specs catalog generate --source .` for local compatibility metadata.
- Run `tessl plugin lint .`, `tessl plugin publish --dry-run .`, then `tessl plugin publish .`.
- Commit the changed source, review records, generated catalog, and plugin manifest together.

## Trust boundary

- Tessl registry publication is the distribution trust boundary.
- The compatibility CLI defaults to the reviewed private registry plugin.
- Local `--source` installs are development-only and still require matching `catalog/reviews/*.json` records unless `--allow-unreviewed` is passed.
- The generated catalog records every file inside each skill directory so local-source installs can verify references and scripts were not changed after catalog generation.

## Versioning

- Pin the registry version, e.g. `cap1-context-specs/context-specs@0.1.0`.
- The target project's `.context-specs/manifest.json` records the registry plugin, version, installed artifact digests, and review authority.
- Re-running `context-specs update --version <version>` moves a project to an explicit reviewed release.

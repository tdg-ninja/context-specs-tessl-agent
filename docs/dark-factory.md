# Dark Factory for Context Specs

Dark Factory is the maintenance harness around the private Tessl plugin
`cap1-context-specs/context-specs`. It keeps the plugin reviewed, publishable,
installable, and safe to roll out.

## What is Tessl in this repo

- **Tessl registry package:** `cap1-context-specs/context-specs@0.1.0`.
- **Tessl workspace:** `cap1-context-specs`.
- **Tessl plugin manifest:** `.tessl-plugin/plugin.json`.
- **Tessl quality review:** `tessl review run quality` for each changed skill.
- **Tessl plugin validation:** `tessl plugin lint .`.
- **Tessl publishing:** `tessl plugin publish .`.
- **Tessl installation:** `tessl install cap1-context-specs/context-specs@<version>`.
- **Tessl Dark Factory agent:** `tessl agent --print` in the maintenance workflow.

Everything else is deterministic local glue: Python digest checks, catalog
generation, compatibility mirroring into `.claude/`, shell smoke tests, and GitHub
PR creation.

## GitHub Actions

- **`validate-catalog.yml` — Non-Tessl deterministic checks**
  - Regenerates the local compatibility catalog.
  - Checks committed catalog drift.
  - Checks review records match current artifact digests.
  - Runs the local-source CLI smoke test.

- **`tessl-plugin-quality.yml` — Tessl review/lint gate**
  - Installs the Tessl CLI.
  - Runs `tessl auth whoami`.
  - Runs `tessl plugin lint .`.
  - Runs `tessl review run quality` for changed skills.
  - Updates review records and regenerates the catalog.

- **`tessl-registry-publish.yml` — Tessl registry release**
  - Verifies review metadata locally.
  - Runs `tessl plugin lint .`.
  - Runs `tessl plugin publish --dry-run .` or `tessl plugin publish .`.
  - Shows `tessl plugin info` after a real publish.

- **`tessl-registry-install-smoke.yml` — Tessl installability check**
  - Installs the Tessl CLI.
  - Runs the wrapper CLI against the private Tessl registry package.
  - Verifies `.tessl/plugins/`, `.claude/skills/`, `.claude/agents/`, and `.context-specs/manifest.json`.

- **`dark-factory-maintenance.yml` — Tessl agent maintenance loop**
  - Runs deterministic preflight checks.
  - Runs `tessl agent --print` with a file-backed prompt.
  - In dry-run mode, produces a maintenance report only.
  - In write mode, allows safe repo edits and opens a PR.
  - Does not publish; publishing stays in `tessl-registry-publish.yml`.

- **`tessl-consumer-rollout.yml` — Tessl registry rollout to another repo**
  - Checks out a target consumer repository.
  - Uses the Context Specs compatibility CLI to install `cap1-context-specs/context-specs@<version>` from the Tessl registry.
  - Verifies installed compatibility files and opens a rollout PR in the consumer repo.

## Required GitHub secrets

- **`TESSL_TOKEN`** — required for all workflows that call Tessl.

The default `GITHUB_TOKEN` is used only by the Dark Factory maintenance workflow
when it needs to push a branch and open a PR. Cross-repository rollout should use
`DARK_FACTORY_GH_TOKEN` with write access to the target repo.

## Manual demo

1. Inspect registry state:
   - `tessl plugin info cap1-context-specs/context-specs@0.1.0`
2. Run deterministic local checks:
   - `python3 bin/context-specs.py catalog generate --source .`
   - `python3 scripts/check-review-records.py --root . --min-score 70`
   - `scripts/test-cli.sh`
3. Run registry install smoke:
   - `scripts/registry-install-smoke.sh`
4. Run Dark Factory in report mode:
   - GitHub Actions → **Dark Factory maintenance** → `dry-run=true`.
5. Publish a release candidate:
   - GitHub Actions → **Tessl registry publish** → `dry-run=true`.
   - Re-run with `dry-run=false` only after the dry run passes.
6. Roll out to a consumer repo:
   - GitHub Actions → **Tessl consumer rollout**.
   - Enter `owner/repo` and the reviewed registry version.

## Operating model

- Use deterministic checks on every PR.
- Use Tessl review/lint on skill or plugin changes.
- Use registry install smoke weekly and before demos.
- Use Dark Factory dry-run weekly for health reports.
- Use Dark Factory write mode only when you want an automated maintenance PR.
- Use publish workflow manually after review metadata and lint are clean.

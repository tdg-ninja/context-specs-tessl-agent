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

- **`tessl-change-verify.yml` — Tessl change verify harness invariant gate**
  - Installs the Tessl CLI.
  - Runs `tessl auth whoami`.
  - Runs `tessl change verify lint` for each verifier JSON file.
  - Runs `tessl change verify --dry-run --all --show-files` to inspect verifier scope.
  - Runs `tessl change verify --github` against the pull request diff.

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

- **`dark-factory-learning.yml` — Tessl agent learning loop**
  - Runs weekly or manually, not on push.
  - Collects recent merged PRs, closed-without-merge PRs, failed workflow runs, review feedback, and Dark Factory issue/PR activity into `.tessl/dark-factory/learning/` files.
  - Runs `tessl agent --print` with a file-backed prompt that references the collected evidence.
  - Uploads a learning report artifact with recurring failure themes and recommended harness improvements.
  - Starts advisory by default; follow-up issue creation is opt-in and capped, and maintenance PR creation is a separate explicit opt-in.
  - Does not publish; publishing stays in `tessl-registry-publish.yml`.

- **`dark-factory-issue-dispatch.yml` — GitHub issue-originated Dark Factory work**
  - Triggers when an issue receives the `dark-factory` label, when someone comments `/dark-factory`, or by manual dispatch with an issue number.
  - Captures the issue body/comments into `.tessl/dark-factory/issue.json`.
  - Validates issue structure twice: a deterministic local check plus a Tessl agent judgment against `docs/github-issue-contract.md`.
  - Stops and comments on the issue when either validation says the issue is not dispatchable.
  - Runs `tessl agent --print` against a file-backed prompt to implement the issue or write a diagnosis.
  - Runs deterministic post-agent checks and opens a PR that references the issue.

- **`tessl-consumer-rollout.yml` — Tessl registry rollout to another repo**
  - Checks out a target consumer repository.
  - Uses the Context Specs compatibility CLI to install `cap1-context-specs/context-specs@<version>` from the Tessl registry.
  - Verifies installed compatibility files and opens a rollout PR in the consumer repo.

## Required GitHub secrets

- **`TESSL_TOKEN`** — required for all workflows that call Tessl.
- **`DARK_FACTORY_GH_TOKEN`** — required for workflows that create or update workflow files, and for cross-repository consumer rollout. Use a token with `repo` and `workflow` scopes.

Dark Factory maintenance and issue-dispatch workflows prefer `DARK_FACTORY_GH_TOKEN`
when pushing branches and opening PRs, then fall back to `GITHUB_TOKEN`. The
fallback works for ordinary same-repo file changes, but GitHub blocks app tokens
from creating or updating `.github/workflows/**` unless the token has `workflow`
scope. Cross-repository rollout should use `DARK_FACTORY_GH_TOKEN` with write
access to the target repo.

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
5. Run the Dark Factory learning loop:
   - GitHub Actions → **Dark Factory learning loop**.
   - Leave issue and PR creation inputs at `false` for advisory reporting.
   - Set `create_follow_up_issues=true` only when you want up to the configured issue cap filed from the learning report.
   - Set `create_maintenance_pr=true` only when you want the agent to make small harness/doc changes and open a PR.
6. Originate work from a GitHub issue:
   - Create an issue with the **Dark Factory task** template or follow `docs/github-issue-contract.md`.
   - Add the `dark-factory` label or comment `/dark-factory`.
   - The issue-dispatch workflow validates the issue shape, runs the Tessl agent, and opens a PR when it makes changes.
7. Publish a release candidate:
   - GitHub Actions → **Tessl registry publish** → `dry-run=true`.
   - Re-run with `dry-run=false` only after the dry run passes.
8. Roll out to a consumer repo:
   - GitHub Actions → **Tessl consumer rollout**.
   - Enter `owner/repo` and the reviewed registry version.

## Operating model

- Use deterministic checks on every PR.
- Use Tessl review/lint on skill or plugin changes.
- Use Tessl change verify on harness invariant changes.
- Use registry install smoke weekly and before demos.
- Use Dark Factory maintenance dry-run weekly for current plugin health reports and clearly scoped upkeep.
- Use Dark Factory learning weekly for evidence-driven harness improvements from merged PRs, failed runs, review feedback, and closed-without-merge work.
- Use Dark Factory write mode only when you want an automated maintenance PR.
- Use learning-loop issue creation only with the explicit opt-in input and bounded issue cap.
- Use GitHub issues plus the `dark-factory` label or `/dark-factory` comment for issue-originated work.
- Use publish workflow manually after review metadata and lint are clean.

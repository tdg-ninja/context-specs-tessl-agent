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
- **Tessl change review:** `tessl change review` with explicit reviewer skills for advisory PR review comments.
- **Tessl change risk:** `tessl change risk` with checked-in `.github/pr-review-gate/` policy for human-review decisions.
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

- **`tessl-change-review.yml` — Tessl advisory PR review**
  - Runs once when a PR opens, reopens, or becomes ready for review; trusted collaborators can rerun with `@tessl-change-review` or workflow dispatch.
  - Rejects cross-repository fork PRs before any secret-backed Tessl setup.
  - Runs `tessl change review --json` with the explicit skill `tessl/code-review#review-code-legibility`.
  - Publishes one advisory GitHub PR review from trusted workflow code and uploads the Tessl JSON artifact.

- **`tessl-change-risk.yml` — Tessl human-confidence/risk decision**
  - Runs when a PR opens, reopens, or becomes ready for review; trusted collaborators can refresh with `@tessl-change-risk` or workflow dispatch.
  - Rejects cross-repository fork PRs before any secret-backed Tessl setup.
  - Runs `tessl change risk --json` using `.github/pr-review-gate/config.json`, `.github/pr-review-gate/policy.md`, and `.github/pr-review-gate/prompt.md`.
  - Publishes an advisory PR comment that states whether human review is required and uploads the Tessl JSON artifact.

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
5. Originate work from a GitHub issue:
   - Create an issue with the **Dark Factory task** template or follow `docs/github-issue-contract.md`.
   - Add the `dark-factory` label or comment `/dark-factory`.
   - The issue-dispatch workflow validates the issue shape, runs the Tessl agent, and opens a PR when it makes changes.
6. Publish a release candidate:
   - GitHub Actions → **Tessl registry publish** → `dry-run=true`.
   - Re-run with `dry-run=false` only after the dry run passes.
7. Roll out to a consumer repo:
   - GitHub Actions → **Tessl consumer rollout**.
   - Enter `owner/repo` and the reviewed registry version.

## Operating model

- Use deterministic checks on every PR.
- Use Tessl review/lint on skill or plugin changes.
- Use Tessl change verify on harness invariant changes.
- Use Tessl change review for advisory review comments from explicit review skills.
- Use Tessl change risk as an advisory human-confidence gate; a `human review required` decision is normal signal, not a failed workflow.
- Keep branch protection unchanged during the advisory rollout. If promoted later, consider requiring these check names: **Tessl change review advisory PR review** and **Tessl change risk human-confidence gate**.
- Use registry install smoke weekly and before demos.
- Use Dark Factory dry-run weekly for health reports.
- Use Dark Factory write mode only when you want an automated maintenance PR.
- Use GitHub issues plus the `dark-factory` label or `/dark-factory` comment for issue-originated work.
- Use publish workflow manually after review metadata and lint are clean.

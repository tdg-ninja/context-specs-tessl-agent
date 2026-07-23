# Dark Factory for Context Specs

Dark Factory is the maintenance harness around the private Tessl plugin
`cap1-context-specs/context-specs`. It keeps the plugin reviewed, publishable,
installable, and safe to roll out.

## What is Tessl in this repo

- **Tessl registry package:** `cap1-context-specs/context-specs@0.1.0`.
- **Tessl workspace:** `cap1-context-specs`.
- **Tessl plugin manifest:** `.tessl-plugin/plugin.json`.
- **Tessl quality review:** `tessl review run quality` for each changed skill.
- **Tessl security review:** `tessl review run security` for new skills and scheduled existing-skill assurance.
- **Tessl evals:** `tessl eval lint .`, `tessl eval run .`, and asynchronous `tessl scenario generate` for repeatable critical workflow behavior checks.
- **Tessl plugin validation:** `tessl plugin lint .`.
- **Tessl publishing:** `tessl plugin publish .`, with a new-skill publish workflow after approved Tessl checks.
- **Tessl installation:** `tessl install cap1-context-specs/context-specs@<version>`.
- **Tessl change review:** `tessl change review` with explicit reviewer skills for advisory PR review comments.
- **Tessl change risk:** `tessl change risk` with checked-in `.github/pr-review-gate/` policy for human-review decisions.
- **Tessl Dark Factory agent:** `tessl agent --print` in the maintenance workflow.
- **Tessl cloud issue implementation skill:** `cap1-context-specs/implement-issue@0.1.0#implement-issue`.

Everything else is deterministic local glue: Python digest checks, catalog
generation, compatibility mirroring into `.claude/`, shell smoke tests, and GitHub
PR creation.

## Human review routing

Dark Factory PRs are authored by automation but merged by people. The fork-local
review owner is `@tdg-ninja`, verified as an administrator of
`tdg-ninja/context-specs-tessl-agent`. `.github/CODEOWNERS` routes all files to
that owner and repeats ownership for governance-sensitive Dark Factory surfaces.

Require human review from `@tdg-ninja` before merging PRs that touch any of these
risky categories:

- **Workflow changes:** `.github/workflows/**` or reviewer-routing files.
- **Auth or token changes:** GitHub permissions, secrets, token names, or setup steps.
- **Verifier policy changes:** `verifiers/**`, `tessl.json`, or verifier-scoped docs.
- **Registry publishing changes:** `.tessl-plugin/**`, `tessl-registry-publish.yml`, or publish/install docs.
- **Dark Factory dispatch changes:** issue validation, prompt wiring, PR creation, or branch/publish behavior.

Use Tessl PR gates as inputs to review, not as replacements for review. A failing
Tessl gate blocks merge until fixed; a passing Tessl gate still needs the human
review above for risky categories.

## Branch protection recommendations for `main`

Recommended required checks:

- **`Non-Tessl deterministic catalog and CLI checks`:** require on PRs that touch
  skills, subagents, catalog data, CLI code, scripts, or workflow dispatch glue.
- **`Tessl change verify harness invariants`:** require on PRs that touch
  workflows, verifier policy, harness docs, issue validation, `tessl.json`,
  skills, or review metadata.
- **`Tessl review/lint gate`:** require on PRs that touch plugin packaging,
  skills, subagents, catalog data, CLI code, scripts, or the quality workflow.

Recommended branch protection settings:

- Require a pull request before merging into `main`.
- Require at least one approval from Code Owners.
- Require review from Code Owners.
- Dismiss stale approvals when new commits are pushed.
- Require conversation resolution before merge.
- Require branches to be up to date before merge when the required checks are enabled.
- Do not enable auto-merge for Dark Factory PRs.

Advisory checks and workflows:

- **`Dark Factory maintenance`:** advisory scheduled/reporting loop; do not make it
  a required merge check.
- **`Dark Factory issue dispatch`:** automation entrypoint that opens work PRs;
  do not make it a required merge check.
- **`Tessl registry install smoke`:** advisory installability signal for demos,
  releases, and scheduled health checks.
- **`Tessl registry publish`:** manual release workflow only; never required for
  ordinary PR merge.
- **`Tessl consumer rollout`:** manual downstream rollout workflow only; never
  required for this repository's `main` branch.

Do not enforce these settings through an API call until the repository owner
confirms the exact required-check names and scope in GitHub branch protection.

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
  - Posts changed-skill quality scores directly on the PR.
  - Runs `tessl review run security` for newly added skills inline.
  - Requires eval coverage and runs `tessl eval run . --skill <new-skill>` for newly added skills.
  - Starts asynchronous eval scenario generation for new skills, with a Tessl agent choosing plugin-vs-repo context and scenario count.
  - Posts PR comments for quality scores, skill assurance, and scenario generation.
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
  - Runs `tessl eval lint .`.
  - Runs `tessl review run security` for changed skills before publishing.
  - Runs `tessl plugin publish --dry-run .` or `tessl plugin publish .`.
  - Shows `tessl plugin info` after a real publish.

- **`tessl-new-skill-publish.yml` — Tessl publish after new skill approval**
  - Runs after pushes to `main` that add skills, or by manual dispatch.
  - Detects newly added skills and requires eval coverage for them.
  - Runs security review, eval lint, full Tessl evals, plugin lint, and metadata checks.
  - Publishes `cap1-context-specs/context-specs` with a patch bump after checks pass; manual dispatch defaults to dry-run.

- **`tessl-registry-install-smoke.yml` — Tessl installability check**
  - Installs the Tessl CLI.
  - Runs the wrapper CLI against the private Tessl registry package.
  - Verifies `.tessl/plugins/`, `.claude/skills/`, `.claude/agents/`, and `.context-specs/manifest.json`.

- **`tessl-evals.yml` — Tessl eval scenarios**
  - Installs the Tessl CLI.
  - Runs `tessl eval lint .` as a deterministic scenario-shape preflight.
  - Runs `tessl eval run .` only when manually dispatched and explicitly requested.
  - Stays advisory by default and does not run on every PR.

- **`tessl-skill-assurance.yml` — Tessl scheduled skill security and evals**
  - Runs weekly and manually.
  - Runs `tessl review run security` for selected skills, defaulting to all existing skills.
  - Runs `tessl eval lint .` and full remote `tessl eval run .` by default for scheduled assurance.
  - Uploads security and eval artifacts for review.

- **`dark-factory-health.yml` — Tessl agent maintenance loop**
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

- **`dark-factory-cloud-issue-dispatch.yml` — Tessl cloud issue implementation**
  - Triggers when an issue receives the `dark-factory-cloud` label, when someone comments `/dark-factory-cloud`, or by manual dispatch with an issue number.
  - Validates issue structure with deterministic local checks.
  - Runs `tessl launch skill --cloud` for the implementation in a Tessl cloud sandbox, instead of running the local `tessl agent --print` workflow on the GitHub Actions runner.

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
3. Validate Tessl eval scenario shape:
   - `tessl eval lint .`
4. Run registry install smoke:
   - `scripts/registry-install-smoke.sh`
5. Run Dark Factory in report mode:
   - GitHub Actions → **Dark Factory maintenance smoke** → `dry_run=true`.
6. Run the Dark Factory learning loop:
   - GitHub Actions → **Dark Factory learning loop**.
   - Leave issue and PR creation inputs at `false` for advisory reporting.
   - Set `create_follow_up_issues=true` only when you want up to the configured issue cap filed from the learning report.
   - Set `create_maintenance_pr=true` only when you want the agent to make small harness/doc changes and open a PR.
7. Originate work from a GitHub issue:
   - Create an issue with the **Dark Factory task** template or follow `docs/github-issue-contract.md`.
   - Add the `dark-factory` label or comment `/dark-factory` to run local implementation with `tessl agent --print` on the GitHub Actions runner.
   - Add the `dark-factory-cloud` label or comment `/dark-factory-cloud` to run cloud implementation with `tessl launch skill --cloud` in a Tessl cloud sandbox.
   - The issue-dispatch workflow validates the issue shape, runs the Tessl agent, and opens a PR when it makes changes.
8. Run critical workflow evals when changing covered behavior:
   - Read `docs/evals.md`.
   - GitHub Actions → **Tessl evals** → keep `run-evals=false` for lint-only, or set `run-evals=true` for a manual advisory eval run.
9. Publish a release candidate:
   - GitHub Actions → **Tessl registry publish** → `dry-run=true`.
   - Re-run with `dry-run=false` only after the dry run passes.
10. Roll out to a consumer repo:
   - GitHub Actions → **Tessl consumer rollout**.
   - Enter `owner/repo` and the reviewed registry version.

## Operating model

- Use deterministic checks on every PR.
- Use Tessl review/lint on skill or plugin changes.
- Use Tessl eval lint on eval changes, automatic eval runs for new skills, asynchronous scenario generation on new-skill PRs, and scheduled full eval runs for existing skills.
- Use Tessl change verify on harness invariant changes.
- Use Tessl change review for advisory review comments from explicit review skills.
- Use Tessl change risk as an advisory human-confidence gate; a `human review required` decision is normal signal, not a failed workflow.
- Keep branch protection unchanged during the advisory rollout. If promoted later, consider requiring these check names: **Tessl change review advisory PR review** and **Tessl change risk human-confidence gate**.
- Use registry install smoke weekly and before demos.
- Use Dark Factory maintenance dry-run weekly for current plugin health reports and clearly scoped upkeep.
- Use Dark Factory learning weekly for evidence-driven harness improvements from merged PRs, failed runs, review feedback, and closed-without-merge work.
- Use Dark Factory write mode only when you want an automated maintenance PR.
- Use learning-loop issue creation only with the explicit opt-in input and bounded issue cap.
- Use GitHub issues plus the `dark-factory` label or `/dark-factory` comment for issue-originated work.
- Use the new-skill publish workflow to publish newly added skills after approved Tessl quality, security, eval, and verifier checks; use registry publish manually for other releases.

# PR Review Gate Policy (starter — conservative)

This policy decides whether a pull request is **low-risk enough to merge
without human review**. It is intentionally strict. Tune it for your repo, but
keep the bar high: the cost of wrongly skipping review is much greater than the
cost of asking for a review that turned out to be unnecessary.

This gate does **not** try to prove a PR is safe. It only decides whether a PR
is clearly low risk enough to skip human review. A "human review required"
result is a normal outcome, not a failure.

## Eligible for no-human-review

A change may skip human review only when **all** of the following hold:

- It is small and surface-level: mostly comments, documentation, copy/string
  wording, formatting, or trivial renames.
- It makes **no meaningful behavior change**: no new logic, no changed control
  flow, no changed outputs for the same inputs.
- It touches **no sensitive paths** (see below).
- It includes **no architectural change**: no new modules, no new dependencies,
  no changes to public interfaces, build, or deployment configuration.
- It includes **no database migration** or schema change.
- It does **not** change authentication, authorization, permissions, or billing.
- Tests are not weakened or deleted; if behavior changed at all, tests cover it.

When in doubt, the change is **not** eligible. Prefer requiring review.

## Always require human review

Require human review whenever the change includes any of:

- Architectural changes, new dependencies, or changes to public APIs/interfaces.
- Changes under sensitive paths: auth/permissions, billing/payments, secrets,
  database migrations, or infrastructure/deployment config.
- Any meaningful behavior change, however small it looks.
- Deleting or weakening tests, or changing source without corresponding tests.
- Changes to this policy or to the PR review gate configuration itself.

## Risk levels

- **low**: docs/comments/copy/formatting only, no behavior change, no sensitive
  paths. Eligible for no-human-review.
- **medium**: real but contained behavior change, or touches non-sensitive
  source/config. Requires human review.
- **high**: sensitive paths, migrations, auth/permission/billing, architectural
  change, or anything you cannot confidently classify. Requires human review.

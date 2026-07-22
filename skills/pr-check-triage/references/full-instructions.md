# pr-check-triage

Triage a red GitHub PR into a short action plan. Do not fix the PR unless the caller asks for implementation after triage.

## Gather check context

- **Target:** PR number, head branch, head SHA, base branch, author, labels, and whether the branch changed during triage.
- **Status overview:** combined PR checks, failing/pending/neutral/skipped statuses, required checks, and mergeability state.
- **Actions runs:** failing workflow names, job names, step names, conclusions, run attempts, timestamps, and rerun history.
- **Failure evidence:** the first real error, surrounding log lines, uploaded artifacts, generated summaries, and linked PR comments.
- **Tessl outputs:** review result JSON, eval results, security review output, change verify/review/risk summaries, and catalog review records when present.
- **Recent context:** changed files, whether failures started on the latest push, and whether the same workflow is failing on other PRs or `main`.

## Classify failures

Use these buckets:

- **Tessl governance:** `tessl change verify`, `tessl change review`, or `tessl change risk` blocks. Treat verifier violations, review findings, and risk policy decisions as code/config/policy work unless logs show Tessl service or auth failure.
- **Tessl skill assurance:** `tessl review run quality`, `tessl review run security`, `tessl eval lint`, `tessl eval run`, skill review metadata, or eval coverage gates. Treat low scores, stale review digests, missing evals, and failing eval criteria as skill/catalog/eval fixes.
- **Registry/package:** plugin lint, catalog generation, review-record validation, install smoke, package metadata, or registry dry-run checks. Treat schema, manifest, digest, packaging, and installability errors as repo config or catalog fixes.
- **Non-Tessl deterministic:** unit tests, lint, typecheck, formatting, shell scripts, schema validators, local smoke checks, and deterministic CI scripts. Treat as code/test/doc fixes; do not rerun unless the logs show a clear flake.
- **Agent/runtime infrastructure:** runner startup, checkout, dependency download outage, auth/secret missing, rate limits, network timeouts, Tessl service unavailable, model/provider errors, or process timeouts without a product failure. Prefer rerun or maintainer/operator action.

## Decide rerun vs fix

Recommend **rerun** only when evidence points to infrastructure: transient network/service errors, runner cancellation, external rate limits, missing logs from startup failure, known flaky dependency download, or a previous successful attempt on the same SHA.

Recommend **fix code/config** when the log contains a reproducible assertion, lint/type/schema error, verifier violation, review-policy failure, stale digest, missing eval, plugin lint error, or package/install contract failure.

Recommend **human maintainer decision** when the failure is a risk gate, security finding, policy ambiguity, missing secret, repository permission issue, or scope question.

## Output format

Keep the summary short and skimmable:

```md
## PR check triage

- **PR / SHA:** #123 at `abc1234`
- **Overall status:** red / pending / blocked, with required checks named
- **Likely root cause:** one sentence
- **Recommendation:** rerun `<check>` / fix code / fix config / maintainer decision

### Failing checks

- **`workflow / job / step`:** bucket; evidence; owner; next action; rerun-or-fix.

### Notes

- Any missing evidence, branch movement, related PR/main failures, or follow-up links.
```

## Boundaries

- Do not paste full logs into the summary; cite the run, job, artifact, or file path.
- Do not mark deterministic failures as flakes without evidence.
- Do not publish Tessl registry versions as part of triage.
- Do not change GitHub Actions, verifiers, review policy, or risk policy during triage.

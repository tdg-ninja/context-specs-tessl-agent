---
name: pr-check-triage
description: Summarize failing GitHub PR checks and recommend the next action for a maintainer or Dark Factory agent. Use when a PR is red and someone needs to distinguish deterministic check failures, Tessl review/verify/risk outcomes, registry/package issues, or agent/runtime infrastructure failures before deciding whether to rerun or fix code/config.
---

# pr-check-triage

Read `references/full-instructions.md`, then produce one concise triage summary.

1. Identify the target PR and current commit SHA.
2. Gather failed or pending PR status checks, GitHub Actions jobs, relevant logs, artifacts, and PR comments.
3. Classify each failure as Tessl governance, Tessl skill assurance, registry/package, Non-Tessl deterministic, or agent/runtime infrastructure.
4. Separate rerunnable infrastructure flakes from failures that need code, config, catalog, eval, verifier, or review-policy fixes.
5. Report failing checks, likely cause, owner/next action, and rerun-vs-fix recommendation.

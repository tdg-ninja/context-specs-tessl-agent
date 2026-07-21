---
name: fix-local-checks
description: Patch the code so `scripts/local-checks.sh` passes, after /implement-mainspec — a narrow post-implement polish specialist. Reads the (remediation-rich) check failures, fixes the underlying cause, never silences a check, re-verifies, and commits. Invoked headless by the dispatcher's two-strike local-checks gate; the dispatcher owns the retry counter. Triggers - fix-local-checks, fix lint, fix local checks, fix typecheck, make checks pass, post-implement polish (project). Use when invoking this Context Specs harness step by name or when the dispatcher reaches this stage of the spec-driven development workflow.
---

# fix-local-checks

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

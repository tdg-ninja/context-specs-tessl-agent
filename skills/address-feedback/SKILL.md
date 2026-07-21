---
name: address-feedback
description: Respond to an automated reviewer's findings on the current feature PR — a narrow, headless responder. Triages each reviewer finding into Clear / Ambiguous / Complex / Out-of-PRD-Scope, then acts — fixes the cause and pushes (diff-only) for Clear, posts one in-thread reply for the rest. Skips findings it already handled. Invoked headless by the dispatcher's feedback gate; the dispatcher owns the round counter and the STUCK escalation. Triggers - address-feedback, address review comments, respond to PR review, handle reviewer findings, PR feedback loop (project). Use when invoking this Context Specs harness step by name or when the dispatcher reaches this stage of the spec-driven development workflow.
---

# address-feedback

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

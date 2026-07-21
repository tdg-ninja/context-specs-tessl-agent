---
name: evaluate-pr
description: Evaluate a PR the harness produced — walk the change, run the system together, and build a firm understanding before you merge it. Use after the harness hands a converged PR to you for review (the "Ready for your review" comment), or any time you want to deeply review an agent-authored PR. The human-attentive skill at the back of the chain; the mirror of /intent. Outcomes — merge, close, or fix-it-yourself-and-push - no handing work back to the loop. Use when invoking this Context Specs harness step by name or when the dispatcher reaches this stage of the spec-driven development workflow.
---

# evaluate-pr

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

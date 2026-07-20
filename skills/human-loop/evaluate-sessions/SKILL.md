---
name: evaluate-sessions
description: Evaluate the build trail of a PR — read the claude -p sessions the harness ran to build it, find where the project's context (Expert / AGENTS.md / skill / spec) served or failed the agents, then capture the learnings as evals (regression tests over the harness's own skills/context) and context fixes. Use when resolving a STUCK (diagnosis-first), auditing how a converged PR was built, or auditing a /learn memory PR. Human-driven and conversational — the trail-evaluating sibling of /evaluate-pr. Outcomes land on a branch (the PR's, or a fresh capture branch if you'll discard the PR) and reach memory via merge + /learn. Triggers - evaluate-sessions, evaluate sessions, review the build trail, diagnose stuck, audit how this was built, session observability.
---

# evaluate-sessions

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

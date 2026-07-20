---
name: implement-mainspec
description: Implements a mainspec end-to-end by auto-detecting mode. Sequential mode (≤3 slices) commits slices in order on the current `feature/<feature>` branch. Parallel mode (>3 slices) uses dependency-aware tiered execution with per-slice worktrees, branches, PRs, and auto-merge into the feature branch. Agent-first — invoked headless by the harness dispatcher with the feature slug as its single argument. No human-in-the-loop, no approval gates.
---

# implement-mainspec

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

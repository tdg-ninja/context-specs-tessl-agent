---
name: implement-slice
description: Implements a single slice with Signal validation and unit tests. Agent-first — invoked by the slice-implementer subagent (under implement-mainspec). No human-in-the-loop; signal validation iterates up to a bounded `max_signal_iterations` (default 3) before reporting FAILURE. Use when invoking this Context Specs harness step by name or when the dispatcher reaches this stage of the spec-driven development workflow.
---

# implement-slice

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

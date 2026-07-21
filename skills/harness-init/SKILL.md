---
name: harness-init
description: One-time, guided setup of the local agent-first coding harness — the polling loop, the deterministic dispatcher, its config, the AGENTS.md contract, and the worktree provisioning that makes per-feature worktrees runnable. Use when a developer wants to set up, bootstrap, install, or initialize the coding harness for the first time in a project.
---

# harness-init

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

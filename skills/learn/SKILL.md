---
name: learn
description: Update the project's long-term memory after a merge to main. Reads the merged diff and the current memory, then writes Expert shards, discovered invariants, candidate lints, and AGENTS.md pointers — all on a reviewable learn/<sha> PR. Use post-merge (the harness invokes it automatically) or with --rebuild to regenerate memory from scratch. Triggers - learn, expert-update, update memory, update expert, post-merge memory, self-improve (project)
---

# learn

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

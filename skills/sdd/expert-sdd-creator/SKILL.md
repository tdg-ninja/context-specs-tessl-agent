---
name: expert-sdd-creator
description: Meta skill for creating new SDD experts from domain documentation. Provide a markdown file path with domain knowledge + optional steering context. Automatically synthesizes references, generates signal scripts, validates, and registers in experts.md/signals.md catalogs. Single-prompt creation with follow-up tweaks. Triggers - create expert, new expert, make expert, expert for, domain expert, add expert (project)
---

# expert-sdd-creator

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

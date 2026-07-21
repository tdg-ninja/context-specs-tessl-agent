---
name: intent
description: Turn an open-ended idea into a PRD plus a runnable definition of done. Use when a developer wants to start a new feature, "file a PRD", "spec out" or "scope" an idea, think through what to build, or kick off the harness for a piece of work. Produces prds/<feature>/prd.md + an executable prds/<feature>/run-prd-test.sh on a prd/<author-slug>/<feature> branch. The one human-attentive skill in the chain.
---

# intent

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

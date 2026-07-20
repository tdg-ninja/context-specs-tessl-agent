---
name: spec-planning
description: Reads a PRD (`prds/<feature>/prd.md`) plus its executable `run-prd-test.sh` (and any helper artifacts under `prds/<feature>/`), grounds them in codebase research, and produces `specs/<feature>/mainspec.md` plus dependency-ordered slices. Encodes the runner as a slice success criterion so implementation completion implies `./prds/<feature>/run-prd-test.sh` exits 0. Touches `specs/<feature>/.planning-done` as its final committed action. Agent-first — no human-in-the-loop.
---

# spec-planning

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

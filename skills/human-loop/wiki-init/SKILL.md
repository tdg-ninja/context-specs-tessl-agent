---
name: wiki-init
description: One-time, guided setup of a standalone LLM-maintained wiki — a Karpathy "LLM Wiki" style knowledge base for a problem domain and your general architecture best practices. Scaffolds an external wiki vault (its own git repo) with /ingest, /query, /lint commands and a conventions doc. Use when a developer wants to start, create, bootstrap, or initialize a wiki / second-brain / knowledge base to understand a problem space before building. The front of the Human Loop's Understanding phase.
---

# wiki-init

Follow this compact workflow. Read `references/full-instructions.md` before making changes or running project commands.

1. Identify the requested feature, PR, merge, or setup target from the user's prompt or dispatcher input.
2. Load the referenced instructions and any files they name for the current step.
3. Do the work on disk using the repo's existing conventions; keep state observable in files, branches, commits, and sentinel markers.
4. Run the required checks or Signal for the step; fix real failures and do not silence gates.
5. Commit or report exactly as the full instructions require, then stop with the next action or handoff.

---
name: implement-mainspec
description: Implements entire mainspecs by auto-detecting the appropriate mode. Sequential mode (≤3 slices) executes slices in order with direct commits. Parallel mode (>3 slices) uses dependency-aware tiered execution, git worktree isolation, per-slice PRs, and tier gating. Use when a user wants to implement a complete mainspec, mentions "implement mainspec" or "implement all slices".
---

# Implement Mainspec

Implements all slices from a mainspec in dependency order. Auto-detects **sequential** (≤3 slices) or **parallel** (>3 slices) mode based on tier computation.

## Workflow Overview

```
Phase 0: Detection — Run compute_tiers.py, check total_slices to select mode

--- SEQUENTIAL MODE (≤3 slices) ---
Phase 1: Parse & Plan — Read mainspec, parse dependency DAG, present simple ordered list for approval
Phase 2: Implement — Delegate each slice to slice-implementer subagent (sequential, foreground). Orchestrator handles git.
Phase 3: Summary — Report final status (simple table, no PR/tier info)

--- PARALLEL MODE (>3 slices) ---
Phase 1: Parse & Plan — Read mainspec, parse dependency DAG, compute tiers, present plan for approval
Phase 2: Feature Branch — Create feature branch, push to remote
Phase 3: Tier 0 — Delegate foundation slices to slice-implementer subagents (sequential, foreground). Orchestrator handles git.
Phase 4: Parallel Tiers — For each subsequent tier: create worktrees, spawn slice-implementer subagents (background), orchestrator handles git after completion
Phase 5: Tier Gate — Pause for review, merge PRs, update feature branch
Phase 6: Summary — Report final status of all slices, PRs, and next steps
```

## Pre-conditions

Validate these before starting:

1. **Mainspec path** — If not provided as argument, ask the user: "Which mainspec would you like to implement? (e.g., `specs/<feature>/mainspec.md`)". Resolve to absolute path: `realpath <mainspec-path>`. All spec file references throughout the workflow use absolute paths.
2. **Git repository** — Must be in a git repo. Error if not.
3. **Git remote** — Must have at least one remote. If no remote exists, warn and offer **local-only mode** — creates branches but skips PR creation.
4. **Clean working tree** — Warn if uncommitted changes exist. Worktrees won't include uncommitted changes from the main working tree.
5. **Worktree gitignore** — Verify `.claude/worktrees/` is in `.gitignore`. If not, add it.

## Phase 0: Mode Detection

Run the tier computation script and check the result to select the execution mode:

```
1. Run: python3 .claude/skills/implement-mainspec/scripts/compute_tiers.py <absolute-mainspec-path>
2. Parse the JSON output which includes:
   - mainspec_name, feature_branch
   - tiers: array of { tier: N, slices: [{ number, name, file }] }
     - file: absolute path to the slice file (can be used directly by subagents)
   - total_slices, max_parallel
3. Mode detection:
   - total_slices ≤ 3 → SEQUENTIAL MODE
   - total_slices > 3  → PARALLEL MODE
4. Present: "Detected <N> slices → <sequential|parallel> mode"
5. User can override: offer "Switch to <other mode>?" option
```

## Phase 1: Parse & Plan

### DAG Parsing

Parse the mainspec's "Slice Dependency Map" table:

| Field | Source | Example |
|-------|--------|---------|
| Slice number | First column, before ` — ` | `3.1` |
| Slice name | First column, after ` — ` | `SVG Path Animation Utilities` |
| Dependencies | "Depends On" column | `3.1` or `—` (none) |
| Blocks | "Blocks" column | `3.2, 3.3, 3.4, 3.5` or `—` (none) |
| Slice file path | From compute_tiers.py output | absolute path to slice file |

The `compute_tiers.py` script handles DAG parsing, topological sort, and tier assignment automatically. The algorithm:

```
1. Start with all slices. remaining = all slices.
2. Tier 0 = slices with no dependencies (Depends On = "—" or "Nothing")
3. Remove Tier 0 from remaining
4. Tier N = slices in remaining whose ALL dependencies are in Tiers 0..N-1
5. Remove Tier N from remaining
6. Repeat until remaining is empty
7. If remaining is not empty and no progress was made → circular dependency error
```

### Plan Presentation

Present the computed plan to the user for approval using `AskUserQuestion`.

**Sequential mode format (≤3 slices):**

```markdown
## Execution Plan: <mainspec-name>

**Mode:** Sequential
**Total slices:** N

### Implementation Order
1. Slice X.Y: <name>
2. Slice X.Y: <name>
3. Slice X.Y: <name>
```

Options: `Approve` / `Modify` / `Cancel`

**Parallel mode format (>3 slices):**

```markdown
## Execution Plan: <mainspec-name>

**Mode:** Parallel
**Feature branch:** `feat/<mainspec-name>`
**Total slices:** N
**Total tiers:** M
**Parallel slices:** X of N slices run in parallel (tiers with >1 slice)

### Tier 0 (Foundation — sequential, direct commit)
- Slice X.Y: <name>

### Tier 1 (Parallel — N subagents)
- Slice X.Y: <name>
- Slice X.Y: <name>

### Tier 2 (Parallel — N subagents)
- Slice X.Y: <name>
```

Options: `Approve` / `Modify` (user can adjust tier assignments) / `Cancel`

## Phase 2: Sequential Implementation

**Applies only to SEQUENTIAL MODE (≤3 slices).**

**Default branch warning:** Before starting, check if the current branch is the default branch (main/master). If so, warn the user: "You are on the default branch (`<branch-name>`). Sequential mode will commit directly to this branch." Offer options:
- `Continue on <branch-name>` — commit directly
- `Create feature branch` — create `feat/<mainspec-name>` first
- `Cancel` — abort

For each slice in dependency order:

1. Create TODO list — One item per slice with sub-items for: Implement, Signal Validation, Unit Tests
2. Mark slice in_progress
3. Delegate to a `slice-implementer` subagent (foreground, NOT background):
   - Use `subagent_type: "slice-implementer"` and `mode: "bypassPermissions"`
   - Use the prompt template from `references/subagent-prompt-template.md` (Sequential Mode section)
   - Set working directory to the repo root
   - Wait for subagent to complete
4. After subagent completes successfully:
   - Orchestrator runs `git add` on changed files (use `git status` to detect changes)
   - Orchestrator runs `git commit -m "Implement slice <number>: <name>"`
5. If subagent reports FAILURE: stop and report to user
6. Mark slice complete

After all slices: skip to Phase 3 (Summary).

## Phase 2–5: Parallel Implementation

**Applies only to PARALLEL MODE (>3 slices).** See below for detailed instructions on each phase:

- **Phase 2 (Feature Branch)** — See "Feature Branch & Git Strategy" section
- **Phase 3 (Tier 0)** — See "Tier 0: Foundation Slices" section
- **Phase 4 (Parallel Tiers)** — See "Parallel Tier Execution" section
- **Phase 5 (Tier Gate)** — See "Tier Gating & Review" section

After all tiers: go to Phase 6 (Summary).

## Feature Branch & Git Strategy

**Applies only to PARALLEL MODE.** Execute after plan approval (Phase 1).

```
1. Identify default branch:
   git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'
   Fallback: try `main`, then `master`

2. Create feature branch:
   git checkout -b feat/<mainspec-name>

3. Push feature branch to remote:
   git push -u origin feat/<mainspec-name>
   (Skip in local-only mode — no remote configured)
```

**Naming conventions:**
- Feature branch: `feat/<mainspec-name>` (e.g., `feat/svg-and-charts`)
- Slice branch: `slice/<number>-<kebab-name>` (e.g., `slice/3.3-barchart`)
- Worktree path: `.claude/worktrees/<mainspec-name>/slice-<number>-<kebab-name>`

**Spec file access:** Spec files are always referenced by absolute path (resolved in Phase 0). Subagents read specs from the original location, not from their worktree. Specs don't need to be in the code repo.

**Git error recovery:**
- Feature branch already exists: `git checkout feat/<mainspec-name>`, resume from existing branch
- Push fails (no remote, auth): warn user, switch to local-only mode
- Slice branch already exists: ask user — reuse or delete and recreate

## Tier 0: Foundation Slices

**Applies only to PARALLEL MODE.** Execute on the feature branch.

Tier 0 slices are delegated to `slice-implementer` subagents sequentially (one at a time, foreground). The orchestrator handles all git operations.

For each Tier 0 slice (in dependency order):

1. Spawn a `slice-implementer` subagent (foreground, NOT background):
   - Use `subagent_type: "slice-implementer"` and `mode: "bypassPermissions"`
   - Use the prompt template from `references/subagent-prompt-template.md` (Tier 0 section)
   - Set working directory to the repo root (subagent works on feature branch directly)
   - Wait for subagent to complete
2. After subagent completes successfully:
   - Orchestrator runs `git status` to detect changed files
   - Orchestrator runs `git add <changed-files>` (only files the subagent created/modified)
   - Orchestrator runs `git commit -m "Implement slice <number>: <name>"`
   - Orchestrator runs `git push origin feat/<mainspec-name>`
3. If subagent reports FAILURE: stop and report to user
4. Proceed to next Tier 0 slice (if multiple foundation slices)

Tier 0 slices are committed directly to the feature branch — no PRs. This is the foundation that all subsequent tiers depend on.

## Worktree Management

**Applies only to PARALLEL MODE.** Create worktrees before spawning subagents for each tier.

**Critical:** Do NOT use `isolation: "worktree"` from the Agent tool — it branches from the remote default branch and won't have Tier 0 code.

### Creating Worktrees

For each slice in the current tier:

```bash
# Derive names from compute_tiers.py output
worktree_name="slice-<number>-<kebab-name>"
branch_name="slice/<number>-<kebab-name>"
worktree_path=".claude/worktrees/<mainspec-name>/${worktree_name}"

# Create worktree branching FROM the feature branch
git worktree add "${worktree_path}" -b "${branch_name}" feat/<mainspec-name>

# Record the absolute worktree path for the subagent prompt
abs_worktree_path="$(realpath ${worktree_path})"
```

### Cleaning Up Worktrees

After PRs are created for a tier (or on error):

```
1. For each worktree: git worktree remove <path>
2. If removal fails (uncommitted changes): warn user, skip cleanup
3. After all tiers complete: git worktree prune
```

## Parallel Tier Execution

**Applies only to PARALLEL MODE.** Execute for each tier after Tier 0.

### 4a. Create Worktrees

Create worktrees for all slices in this tier per the Worktree Management section above.

### 4b. Spawn Subagents

Read `references/subagent-prompt-template.md` for the full prompt template.

Spawn one background subagent per slice:
- Use the Agent tool with `run_in_background: true`
- Use `subagent_type: "slice-implementer"` and `mode: "bypassPermissions"`
- Do NOT use `isolation: "worktree"` (worktree already created in 4a)
- Spawn all subagents for this tier in a SINGLE message (maximizes parallelism)
- Capture the agent_id / task_id for each subagent

**Batching:** If a tier has more than 7 slices, split into batches of up to 7. Spawn batch 1, wait for all to complete, then spawn batch 2.

### 4c. Wait for Completion

- Subagents will notify when done (automatic delivery)
- Alternatively, use `TaskOutput(task_id=<id>, block=true)` per subagent
- Collect results: success/failure per slice

### 4d. Git Operations (Orchestrator)

After all subagents for the tier complete, the orchestrator handles git for each worktree:

```
For each successful slice in the tier:
1. cd <worktree-absolute-path>
2. git status  (detect changed files)
3. git add <changed-files>  (only files the subagent created/modified, NOT git add -A)
4. git commit -m "Implement slice <number>: <name>"
5. git push -u origin <branch-name>
```

### 4e. Handle Failures

- If a subagent fails, log the slice number and error details
- Other subagents in the same tier are NOT affected
- Mark failed slice for user decision (retry / skip / abort)
- Read `references/error-handling.md` for detailed recovery procedures

## Tier Gating & Review

**Applies only to PARALLEL MODE.** Execute after each tier's subagents complete.

### 5a. Create PRs

For each successfully completed slice in the current tier:

```bash
gh pr create \
  --head slice/<number>-<kebab-name> \
  --base feat/<mainspec-name> \
  --title "Slice <number>: <name>" \
  --body "## Summary
- Implements slice <number> of <mainspec-name>
- Part of Tier <N>

## Signal Validation
<Signal Skill: name or None> — <passed / skipped>

---
**Target:** feat/<mainspec-name>"
```

Create all PRs for the tier in parallel.

### 5b. Report PRs

Report PR URLs to user. If any slices failed, also report failures with error summary.

### 5c. Tier Gate

Ask user how to proceed using `AskUserQuestion`:
- **Review & merge** — Pause for PR review, then merge to feature branch
- **Stop here** — Halt execution, preserve branches and PRs for later

### 5d. Merge Process

Merge PRs one at a time (ordered by slice number):

```
1. gh pr merge <pr-number> --merge
2. git pull origin feat/<mainspec-name>
3. If merge conflict: attempt auto-resolution for simple conflicts
   (barrel exports, registry additions, import lists)
   If complex: report to user and ask for guidance
4. Continue with remaining PRs
```

### 5e. After Merge

```
1. git checkout feat/<mainspec-name> && git pull
2. Clean up worktrees: git worktree remove <path> for each
3. Proceed to next tier (loop back to Phase 4)
```

Subsequent tier worktrees branch from the updated feature branch, so all previous tier PRs must be merged first.

## Phase 3/6: Summary Report

**Sequential mode summary:**

```markdown
## Implementation Complete: <mainspec-name>

| Slice | Status | Tests |
|-------|--------|-------|
| X.Y <name> | ✅ Done | ✅ Passing |
```

**Parallel mode summary:**

```markdown
## Implementation Complete: <mainspec-name>

**Feature branch:** `feat/<mainspec-name>`

| Tier | Slice | Status | PR | Tests |
|------|-------|--------|----|-------|
| 0 | X.Y <name> | ✅ Committed | — | ✅ |
| 1 | X.Y <name> | ✅ PR Created | #123 | ✅ |

### Next Steps
- Review and merge open PRs to `feat/<mainspec-name>`
- When ready, PR `feat/<mainspec-name>` → `main`
- Read `references/release-strategy.md` for merge-back instructions
```

## Signal Processing

Signal skills provide runtime feedback during implementation. They validate that code works correctly in real environments.

### Reading the Signal Section

Each slice includes a Signal section after the Objective:

```
## Signal

**Signal Skill:** {signal-skill-name | None}

**Expected Behavior:**
- what should succeed when correctly implemented
```

### Signal Workflow

1. After implementing slice code, check the Signal section
2. If Signal Skill is specified:
   - Invoke the signal: `skill: "{signal-name}"`
   - Wait for signal output
   - Follow the guidance from Signal
3. If signal indicates success: Continue to unit tests
4. If signal indicates failure:
   - Review signal output to identify specific issue
   - Fix the implementation
   - Re-invoke signal
   - Repeat until signal validates success
5. If Signal Skill is "None": Skip signal validation, proceed to unit tests

## TODO Structure

**Sequential mode:**
```
[ ] X.Y-<slice-name> - Implement
[ ] X.Y-<slice-name> - Signal Validation
[ ] X.Y-<slice-name> - Unit Tests
...
```

**Parallel mode:**
```
[ ] Phase 0 - Mode Detection
[ ] Phase 1 - Plan Presentation & Approval
[ ] Phase 2 - Feature Branch Creation
[ ] Tier 0: X.Y-<slice-name> - Delegate to slice-implementer
[ ] Tier 0: X.Y-<slice-name> - Git commit & push
[ ] Tier 1: Create worktrees
[ ] Tier 1: Spawn slice-implementer subagents (N slices)
[ ] Tier 1: Wait for completion
[ ] Tier 1: Git commit & push for each worktree
[ ] Tier 1: Create PRs
[ ] Tier 1: Gate — Review & Merge
...
[ ] Phase 6 - Summary Report
```

## References

Detailed reference material for parallel mode execution:

- **Subagent prompt template**: Read `references/subagent-prompt-template.md` when spawning subagents in Phase 4
- **Error handling**: Read `references/error-handling.md` when any phase encounters errors
- **Release strategy**: Read `references/release-strategy.md` when presenting the summary report or when the user asks about releasing

## Guidelines

### Both Modes

**DO:**
- Present the execution plan for approval before implementation
- Use absolute paths for all spec file references
- Delegate slice implementation to `slice-implementer` subagents — orchestrator stays lean
- Use `subagent_type: "slice-implementer"` and `mode: "bypassPermissions"` for all subagent spawns
- Handle all git operations (add, commit, push) in the orchestrator — subagents do NOT run git
- Use `git status` to detect changed files after subagent completion
- Read only the current slice file — never read all slices at once

**DON'T:**
- Implement slices inline — always delegate to `slice-implementer` subagent
- Read files to embed in subagent prompts — subagents read their own files
- Skip slices or implement out of order
- Proceed with failing tests
- Over-engineer beyond slice scope
- Skip signal validation when a signal is specified
- Ignore signal failure indicators

### Sequential Mode Only

**DON'T:**
- Create feature branches (work on current branch)
- Create PRs for individual slices
- Create worktrees

### Parallel Mode Only

**DO:**
- Spawn all subagents for a tier in a single message
- Clean up worktrees after PRs are created
- Check for existing branches/PRs when resuming a partial run

**DON'T:**
- Use `isolation: "worktree"` — it branches from default branch, missing Tier 0 code
- Skip tier gating — all PRs must be merged before next tier
- Create PRs targeting main — always target the feature branch
- Spawn more than 7 subagents simultaneously (batch if needed)
- Eagerly merge main into feat after release — only when needed for conflicts
---
name: implement-mainspec
description: Implements a mainspec end-to-end by auto-detecting mode. Sequential mode (≤3 slices) commits slices in order on the current `feature/<feature>` branch. Parallel mode (>3 slices) uses dependency-aware tiered execution with per-slice worktrees, branches, PRs, and auto-merge into the feature branch. Agent-first — invoked headless by the harness dispatcher with the feature slug as its single argument. No human-in-the-loop, no approval gates.
---

# Implement Mainspec

Implements all slices from a mainspec in dependency order. Auto-detects **sequential** (≤3 slices) or **parallel** (>3 slices) mode based on tier computation. Agent-first: invoked headless by the harness dispatcher, runs end-to-end with no approval gates, exits.

## Invocation Contract

**Invoked by the dispatcher as:** `claude -p "/implement-mainspec <feature>"`, run from inside the feature worktree (the dispatcher `cd`s into it — there is no print-mode `--cwd` flag).

**Single argument:** `<feature>` — kebab-case feature slug. The mainspec path is `specs/<feature>/mainspec.md` relative to cwd.

**Inputs read from disk (paths relative to cwd):**
- `specs/<feature>/mainspec.md`
- `specs/<feature>/slices/*.md`
- Current `feature/<feature>` branch state (worktree HEAD).

**Outputs to disk / remote:**
- Per-slice branches `slice/<number>-<kebab-name>` pushed to origin (**not deleted after merge** — they remain as archaeological evidence so the eventual `feature/<feature> → main` PR review can trace which commits belong to which slice).
- Per-slice PRs merged into `feature/<feature>` with `gh pr merge --merge` (preserves slice commits + a merge commit).
- All implementation code committed and pushed on `feature/<feature>`.

**No sentinel.** The dispatcher's success signal for this step is `./prds/<feature>/run-prd-test.sh` exits 0, verified externally. The PRD test is encoded into a slice's Signal by spec-planning, so completing all slices implies the PRD test passes. We do not write a sentinel file.

**Idempotency:**
- On every invocation, inspect `feature/<feature>` git history. Determine which slices are already merged (look for merge commits like `Merge slice/<n>-<name>` or branches whose commits match slice scope).
- Compute the remaining slices via the DAG (`compute_tiers.py`) minus the already-merged set.
- Work only on remaining slices.
- If all slices appear merged, exit cleanly. The dispatcher will re-verify the PRD test externally.

**No approval gates anywhere.** No `AskUserQuestion` for plan approval, default-branch warning, tier review, retry decisions, or branch-state ambiguity. Every decision is deterministic or deferred to the next dispatcher tick.

## Workflow Overview

```
Phase 0: Detection — Run compute_tiers.py, check total_slices to select mode
Phase 1: Parse & Resume — Read mainspec, parse DAG, inspect feature/<feature> for already-merged slices

--- SEQUENTIAL MODE (≤3 slices) ---
Phase 2: Implement — Delegate each remaining slice to slice-implementer subagent (sequential, foreground). Orchestrator handles git directly on feature/<feature>.
Phase 3: Log — Log final status of this invocation to stdout for observability

--- PARALLEL MODE (>3 slices) ---
Phase 2: Tier 0 — Delegate foundation slices to slice-implementer subagents (sequential, foreground). Orchestrator handles git directly on feature/<feature>.
Phase 3: Parallel Tiers — For each subsequent tier: create worktrees, spawn slice-implementer subagents (background), orchestrator handles git after completion.
Phase 4: Auto-Merge — Create PRs and auto-merge into feature/<feature> with `gh pr merge --merge`. Branches are NOT deleted on merge.
Phase 5: Log — Log final status of this invocation to stdout for observability
```

## Pre-conditions

The dispatcher guarantees a clean worktree on `feature/<feature>` before invoking. Verify deterministically and exit on violation — the dispatcher will re-derive state on the next tick.

1. **Git repository** — `git rev-parse --git-dir` succeeds. If not, exit non-zero.
2. **Current branch matches `feature/<feature>`** — must match the argument exactly. If not, exit. (Never create the feature branch; the dispatcher's atomic rename from `prd/<author>/<feature>` did that.)
3. **Clean working tree** — `git status --porcelain` empty. If not, exit (the dispatcher's wipe should guarantee this; if it trips, something upstream is wrong).
4. **Remote configured** — `git remote get-url origin` succeeds. If not, exit. Parallel mode requires remote.
5. **Worktree gitignore** — verify `.claude/worktrees/` is in `.gitignore`. Auto-append if missing (idempotent; no prompt).

## Phase 0: Mode Detection

Run the tier computation script and select the execution mode deterministically:

```
1. Run: python3 .claude/skills/implement-mainspec/scripts/compute_tiers.py specs/<feature>/mainspec.md
2. Parse the JSON output which includes:
   - mainspec_name, feature_branch
   - tiers: array of { tier: N, slices: [{ number, name, file }] }
     - file: absolute path to the slice file (can be used directly by subagents)
   - total_slices, max_parallel
3. Mode detection (no override, no prompt):
   - total_slices ≤ 3 → SEQUENTIAL MODE
   - total_slices > 3  → PARALLEL MODE
4. Log to stdout: "Detected <N> slices → <sequential|parallel> mode" for observability.
```

## Phase 1: Parse & Resume

### DAG Parsing

`compute_tiers.py` parses the mainspec's "Slice Dependency Map" table:

| Field | Source | Example |
|-------|--------|---------|
| Slice number | First column, before ` — ` | `3.1` |
| Slice name | First column, after ` — ` | `SVG Path Animation Utilities` |
| Dependencies | "Depends On" column | `3.1` or `—` (none) |
| Blocks | "Blocks" column | `3.2, 3.3, 3.4, 3.5` or `—` (none) |
| Slice file path | From compute_tiers.py output | absolute path to slice file |

The script handles topological sort and tier assignment via the algorithm:

```
1. Start with all slices. remaining = all slices.
2. Tier 0 = slices with no dependencies (Depends On = "—" or "Nothing")
3. Remove Tier 0 from remaining
4. Tier N = slices in remaining whose ALL dependencies are in Tiers 0..N-1
5. Remove Tier N from remaining
6. Repeat until remaining is empty
7. If remaining is not empty and no progress was made → circular dependency error
```

### Resume detection (idempotency)

Before implementing anything, inspect what's already merged on `feature/<feature>`:

```
1. git fetch origin
2. For each slice in the mainspec DAG:
   - Check whether a merge commit referencing `slice/<number>-<kebab-name>` exists in
     `git log feature/<feature>` (e.g., `git log --merges --grep "slice/<number>-"`).
   - If yes, mark slice as ALREADY-MERGED. Skip it.
   - Otherwise, mark slice as REMAINING.
3. If all slices are ALREADY-MERGED, log "all slices merged, nothing to do" and exit cleanly.
4. Otherwise, proceed with REMAINING slices in their original tier assignments.
```

### Plan logging (no approval)

Log the computed plan to stdout for observability — what mode, which tiers, which slices are remaining vs. already-merged. **No approval gate, no `AskUserQuestion`.** Proceed directly to Phase 2.

**Sequential mode log format:**

```
## Execution Plan: <mainspec-name>
Mode: Sequential
Total slices: N (already-merged: M, remaining: K)
Remaining order:
1. Slice X.Y: <name>
2. Slice X.Y: <name>
```

**Parallel mode log format:**

```
## Execution Plan: <mainspec-name>
Mode: Parallel
Feature branch: feature/<feature>
Total slices: N (already-merged: M, remaining: K)
Total tiers: T (remaining tiers to process: T')
Tier 0 (Foundation): X.Y <name>, X.Y <name>
Tier 1 (Parallel — N subagents): X.Y <name>, X.Y <name>
Tier 2 (Parallel — N subagents): X.Y <name>
```

## Phase 2: Sequential Implementation

**Applies only to SEQUENTIAL MODE (≤3 slices).** The preconditions section already guaranteed we are on `feature/<feature>`, so we commit directly to it. No default-branch warning, no approval prompt.

For each **REMAINING** slice in dependency order (skipping already-merged ones from Phase 1):

1. Create TODO list — One item per slice with sub-items for: Implement, Signal Validation, Unit Tests.
2. Mark slice in_progress.
3. Delegate to a `slice-implementer` subagent (foreground, NOT background):
   - Use `subagent_type: "slice-implementer"` and `mode: "bypassPermissions"`.
   - Use the prompt template from `references/subagent-prompt-template.md` (Sequential Mode section). The template passes `max_signal_iterations: 3` to bound the inner signal-fix loop.
   - Set working directory to the repo root.
   - Wait for subagent to complete.
4. After subagent completes successfully:
   - Orchestrator runs `git status` to detect changes.
   - Orchestrator runs `git add <changed-files>` (only files the subagent created/modified).
   - Orchestrator runs `git commit -m "Implement slice <number>: <name>"`.
   - Orchestrator runs `git push origin feature/<feature>`.
5. If subagent reports FAILURE:
   - Log the failure (slice number, error text) to stdout.
   - Commit any safe partial work attributable to a completed earlier slice (we should never have partial state at this point since each slice's commits happen synchronously after subagent success — but if `git status` shows changes, they should not be committed).
   - Exit. The dispatcher will re-fire on the next tick; idempotency in Phase 1 will skip the already-completed slices and retry this one.
6. Mark slice complete.

After all remaining slices: proceed to Phase 3 (Log).

## Phases 2–5: Parallel Implementation

**Applies only to PARALLEL MODE (>3 slices).** See below for detailed instructions:

- **Phase 2 (Tier 0)** — See "Tier 0: Foundation Slices" section.
- **Phase 3 (Parallel Tiers)** — See "Parallel Tier Execution" section.
- **Phase 4 (Auto-Merge)** — See "Tier Auto-Merge" section.
- **Phase 5 (Log)** — Stdout log only.

## Feature Branch Verification & Git Strategy

**Applies only to PARALLEL MODE.** The dispatcher's atomic rename already created `feature/<feature>` before this skill ran. We verify and proceed; we never create the feature branch.

```
1. Verify HEAD branch == feature/<feature>:
   actual="$(git rev-parse --abbrev-ref HEAD)"
   [[ "${actual}" == "feature/<feature>" ]] || exit 1
2. Verify the branch tracks origin:
   git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1 || git push -u origin feature/<feature>
```

**Naming conventions:**
- Feature branch: `feature/<feature>` (e.g., `feature/svg-and-charts`).
- Slice branch: `slice/<number>-<kebab-name>` (e.g., `slice/3.3-barchart`).
- Worktree path: `.claude/worktrees/<feature>/slice-<number>-<kebab-name>`.

**Spec file access:** Spec files are referenced by absolute path (resolved from `compute_tiers.py` output). Subagents read specs from the original location, not from their worktree.

**Git state recovery (deterministic, no prompts):**
- Feature branch exists locally and matches origin: proceed.
- Feature branch exists but is behind origin: `git pull --ff-only origin feature/<feature>` before any tier work.
- Slice branch already exists on origin: this means a prior `/implement-mainspec` tick was interrupted. Check whether the corresponding PR is merged via `gh pr view slice/<number>-<kebab-name> --json state -q .state`:
  - State `MERGED` → slice is done; skip it.
  - State `OPEN` → PR was created but not merged; auto-merge it as part of Phase 4.
  - No PR found → branch has commits but no PR; create the PR in Phase 4 and proceed.
  - Branch exists with no commits past `feature/<feature>` HEAD → unusable, but harmless; recreate the worktree on top.

## Tier 0: Foundation Slices

**Applies only to PARALLEL MODE.** Execute on `feature/<feature>` directly.

Tier 0 slices are delegated to `slice-implementer` subagents sequentially (one at a time, foreground). The orchestrator handles all git operations.

For each REMAINING Tier 0 slice (in dependency order):

1. Spawn a `slice-implementer` subagent (foreground, NOT background):
   - Use `subagent_type: "slice-implementer"` and `mode: "bypassPermissions"`.
   - Use the prompt template from `references/subagent-prompt-template.md` (Tier 0 section).
   - Set working directory to the repo root (subagent works on feature branch directly).
   - Wait for subagent to complete.
2. After subagent completes successfully:
   - Orchestrator runs `git status` to detect changed files.
   - Orchestrator runs `git add <changed-files>` (only files the subagent created/modified).
   - Orchestrator runs `git commit -m "Implement slice <number>: <name>"`.
   - Orchestrator runs `git push origin feature/<feature>`.
3. If subagent reports FAILURE:
   - Log the failure.
   - Do not commit any subagent partial state.
   - Exit. Dispatcher will re-fire; idempotency will skip merged work and retry this slice.
4. Proceed to next Tier 0 slice (if multiple foundation slices).

Tier 0 slices are committed directly to `feature/<feature>` — no PRs. This is the foundation that all subsequent tiers depend on.

## Worktree Management

**Applies only to PARALLEL MODE.** Create worktrees before spawning subagents for each tier.

**Critical:** Do NOT use `isolation: "worktree"` from the Agent tool — it branches from the remote default branch and won't have Tier 0 code.

### Creating Worktrees

For each REMAINING slice in the current tier (skip slices whose PR is already merged):

```bash
# Derive names from compute_tiers.py output
worktree_name="slice-<number>-<kebab-name>"
branch_name="slice/<number>-<kebab-name>"
worktree_path=".claude/worktrees/<feature>/${worktree_name}"

# Create worktree branching FROM the feature branch.
# If branch already exists locally or on origin, attach without -b.
if git show-ref --verify --quiet "refs/heads/${branch_name}" \
   || git show-ref --verify --quiet "refs/remotes/origin/${branch_name}"; then
  git worktree add "${worktree_path}" "${branch_name}"
else
  git worktree add "${worktree_path}" -b "${branch_name}" feature/<feature>
fi

# Record the absolute worktree path for the subagent prompt
abs_worktree_path="$(realpath ${worktree_path})"
```

### Cleaning Up Worktrees

After PRs for a tier have been merged (or on a controlled exit):

```
1. For each worktree: git worktree remove <path>
2. If removal fails (uncommitted changes): log the failure and exit.
   The dispatcher's next tick will wipe state and re-derive what to do.
3. After all tiers complete: git worktree prune
```

## Parallel Tier Execution

**Applies only to PARALLEL MODE.** Execute for each REMAINING tier after Tier 0.

### 3a. Create Worktrees

Create worktrees for all REMAINING slices in this tier per the Worktree Management section above.

### 3b. Spawn Subagents

Read `references/subagent-prompt-template.md` for the full prompt template.

Spawn one background subagent per slice:
- Use the Agent tool with `run_in_background: true`.
- Use `subagent_type: "slice-implementer"` and `mode: "bypassPermissions"`.
- Do NOT use `isolation: "worktree"` (worktree already created in 3a).
- Spawn all subagents for this tier in a SINGLE message (maximizes parallelism).
- Capture the agent_id / task_id for each subagent.
- The prompt template includes `max_signal_iterations: 3` to bound the inner signal-fix loop.

**Batching:** If a tier has more than 7 slices, split into batches of up to 7. Spawn batch 1, wait for all to complete, then spawn batch 2.

### 3c. Wait for Completion

- Subagents will notify when done (automatic delivery).
- Alternatively, use `TaskOutput(task_id=<id>, block=true)` per subagent.
- Collect results: success/failure per slice.

### 3d. Git Operations (Orchestrator)

After all subagents for the tier complete, the orchestrator handles git for each worktree of a successful slice:

```
For each successful slice in the tier:
1. cd <worktree-absolute-path>
2. git status  (detect changed files)
3. git add <changed-files>  (only files the subagent created/modified, NOT git add -A)
4. git commit -m "Implement slice <number>: <name>"
5. git push -u origin <branch-name>
```

### 3e. Handle Failures

- If a subagent fails, log the slice number and error details to stdout.
- Other subagents in the same tier are NOT affected — they finish their work.
- The failed slice will NOT get a PR in Phase 4.
- Read `references/error-handling.md` for detailed recovery procedures.

## Tier Auto-Merge

**Applies only to PARALLEL MODE.** Execute after each tier's subagents complete and orchestrator git operations finish. There is no review gate, no `AskUserQuestion`, no "Review & merge / Stop here" prompt. Slice PRs are created and merged automatically.

### 4a. Create PRs

For each successfully completed slice in the current tier whose PR does not already exist:

```bash
gh pr create \
  --head slice/<number>-<kebab-name> \
  --base feature/<feature> \
  --title "Slice <number>: <name>" \
  --body "Implements slice <number> of <feature>. Part of Tier <N>.

Signal: <Signal Skill: name or None> — <passed / skipped>"
```

Create all PRs for the tier in parallel.

### 4b. Auto-Merge PRs

For each PR (in slice-number order):

```bash
gh pr merge <pr-number> --merge
```

**Key constraints:**
- Use `--merge` (NOT `--squash`) — preserves the slice's individual commits plus a merge commit. The merge commit clearly delineates which commits belong to which slice when reviewing the eventual `feature/<feature> → main` PR.
- **Do NOT pass `--delete-branch`** — slice branches stay on origin as archaeological evidence. Reviewers of the feature→main PR can navigate to `slice/<n>-<name>` to see the focused, in-context diff for any slice.

After each successful merge:
- `git pull origin feature/<feature>` in the orchestrator's checkout to bring the merged commits in.

### 4c. Handle Merge Conflicts

If `gh pr merge` fails for conflict reasons:
- Attempt automatic resolution for simple conflicts (barrel exports, registry additions, import lists). Same heuristic patterns as the historical code.
- If unresolvable: log which PR failed and which files conflicted, then exit. The dispatcher will re-fire `/implement-mainspec` on the next tick; that invocation's idempotency check will see the failed PR is still open and either retry the merge (if origin now has the prerequisite commits) or skip if the work has moved on.

### 4d. Worktree Cleanup

After all PRs for the tier are merged:
- `git worktree remove <path>` for each slice worktree in this tier.
- Continue to the next tier (subsequent-tier worktrees branch from the updated `feature/<feature>`).

### 4e. Failed Slices Within a Tier

If any slice in the tier failed in Phase 3 (slice-implementer reported FAILURE):
- Do not create a PR for it.
- Log the failure to stdout with slice number and error details.
- The other tier slices proceed normally through PR creation and auto-merge.
- After the tier completes auto-merge, exit. The dispatcher will re-fire on the next tick; idempotency in Phase 1 will identify the failed slice as REMAINING and retry it. Subsequent tiers must wait until this tier is fully merged, so the exit is the correct behavior.

## Phase 3/5: Stdout Log (Observability Only)

There is no human to report to. Write a concise stdout log of what this invocation did so the dispatcher's log is readable. The dispatcher does not parse this output; it only checks `./prds/<feature>/run-prd-test.sh` exit code externally.

**Sequential mode log:**

```
## /implement-mainspec invocation summary: <feature>
Mode: Sequential
Skipped (already-merged): <list of slice numbers> (or none)
Implemented this invocation: <list of slice numbers>
Failed this invocation: <list of slice numbers> (or none)
Branch: feature/<feature> (pushed)
```

**Parallel mode log:**

```
## /implement-mainspec invocation summary: <feature>
Mode: Parallel
Feature branch: feature/<feature>
Skipped (already-merged): <list of slice numbers> (or none)
Tier 0 implemented: <list>
Tier 1 implemented (auto-merged): <list of PRs merged>
Tier 2 implemented (auto-merged): <list of PRs merged>
...
Failed this invocation: <list of slice numbers + reasons> (or none)

If failures: dispatcher will re-fire on next tick; idempotency will skip merged work.
If no failures: dispatcher will verify `./prds/<feature>/run-prd-test.sh` exits 0 on next tick.
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
[ ] Phase 1 - Parse DAG & resume detection
[ ] Phase 2 - Tier 0 foundation slices (sequential)
[ ] Tier 0: X.Y-<slice-name> - Delegate to slice-implementer
[ ] Tier 0: X.Y-<slice-name> - Git commit & push
[ ] Tier 1: Create worktrees
[ ] Tier 1: Spawn slice-implementer subagents (N slices)
[ ] Tier 1: Wait for completion
[ ] Tier 1: Git commit & push for each worktree
[ ] Tier 1: Create PRs
[ ] Tier 1: Auto-merge PRs (`gh pr merge --merge`)
[ ] Tier 1: Worktree cleanup
...
[ ] Phase 5 - Stdout log
```

## References

Detailed reference material for parallel mode execution:

- **Subagent prompt template**: Read `references/subagent-prompt-template.md` when spawning subagents in Phase 4
- **Error handling**: Read `references/error-handling.md` when any phase encounters errors
- **Release strategy**: Read `references/release-strategy.md` when presenting the summary report or when the user asks about releasing

## Guidelines

### Both Modes

**DO:**
- Log the execution plan to stdout for observability (no approval gate; proceed directly).
- Use absolute paths for all spec file references.
- Delegate slice implementation to `slice-implementer` subagents — orchestrator stays lean.
- Use `subagent_type: "slice-implementer"` and `mode: "bypassPermissions"` for all subagent spawns.
- Pass `max_signal_iterations: 3` to each subagent (via the prompt template) so the inner signal-fix loop is bounded.
- Handle all git operations (add, commit, push) in the orchestrator — subagents do NOT run git.
- Use `git status` to detect changed files after subagent completion.
- Read only the current slice file — never read all slices at once.
- Treat the current branch as the feature branch (must match `feature/<feature>`); never create it.
- Inspect `feature/<feature>` git history at the start of every invocation to determine which slices are already merged; idempotency depends on this.
- On any failure (subagent FAILURE, merge conflict, etc.): log clearly, commit any safe partial state, exit. The dispatcher's next tick is the retry mechanism.

**DON'T:**
- Use `AskUserQuestion` anywhere. The dispatcher provides no input, and the human is not in the loop.
- Implement slices inline — always delegate to `slice-implementer` subagent.
- Read files to embed in subagent prompts — subagents read their own files.
- Skip slices or implement out of order (within remaining work).
- Proceed with failing tests.
- Over-engineer beyond slice scope.
- Skip signal validation when a signal is specified.
- Ignore signal failure indicators.
- Create a sentinel file for this skill. The dispatcher's success check is `./prds/<feature>/run-prd-test.sh` exit code, not a sentinel.

### Sequential Mode Only

**DON'T:**
- Create PRs for individual slices.
- Create worktrees.

### Parallel Mode Only

**DO:**
- Spawn all subagents for a tier in a single message.
- Auto-merge slice PRs with `gh pr merge --merge` (preserving slice commits + a merge commit). Never `--squash`. Never `--delete-branch` — slice branches stay on origin as evidence.
- Clean up worktrees after each tier's PRs are merged.
- Check for existing slice branches/PRs at the start of every invocation; reuse merged ones (skip), reuse open ones (continue auto-merge), recreate branchless ones from `feature/<feature>`.

**DON'T:**
- Use `isolation: "worktree"` — it branches from default branch, missing Tier 0 code.
- Create PRs targeting `main` — always target `feature/<feature>`.
- Spawn more than 7 subagents simultaneously (batch if needed).
- Pause for human tier review — there is no human; auto-merge each tier and continue.
- Eagerly merge `main` into `feature/<feature>` — only when needed for conflicts during the eventual feature→main PR.
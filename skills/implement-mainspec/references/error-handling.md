# Error Handling & Recovery

Reference for handling errors during mainspec implementation. Read this when any phase encounters errors.

Agent-first model: there is no human in the loop and no orchestrator session waiting on stdout. The retry mechanism is the harness dispatcher: each tick wipes uncommitted state in the worktree and re-invokes `/implement-mainspec`. Idempotency (Phase 1 resume detection) is what makes retries safe — the skill identifies which slices are already merged and works only on remaining ones.

## 1. Subagent Fails Implementation

- Log error details from subagent output to stdout for observability.
- Mark the slice as failed for this invocation; do not create a PR for it.
- Other slices in the same tier are NOT affected — let them finish and auto-merge.
- After the tier finishes auto-merge, exit. The dispatcher's next tick will re-fire `/implement-mainspec`; Phase 1's idempotency check will skip merged slices and retry this one.
- There is no skill-level retry cap. The dispatcher has no attempt counter for this skill (only for `local-checks`). If the same slice keeps failing across many ticks, that is an observability concern, not a skill-design concern.

## 2. Signal Validation Fails Inside Subagent

- The subagent's `implement-slice` workflow handles this via the bounded inner loop (`max_signal_iterations: 3` — fix code, re-invoke signal, repeat up to 3 times).
- If the cap is hit, the subagent returns FAILURE with `reason: signal_failure` and the last signal output.
- Treat this like §1 — mark slice failed, let tier finish, exit, dispatcher re-fires.

## 3. PR Creation Fails

- Usually means the slice branch wasn't pushed or origin is unavailable.
- Log error, continue creating PRs for other slices in the tier.
- The next dispatcher tick will re-enter Phase 4; idempotency will detect the missing PR and retry creation.

## 4. Tier Auto-Merge — Out-of-Order or Missing Dependency

- With auto-merge, the orchestrator processes PRs in slice-number order within each tier, and only moves to the next tier after the current tier is fully merged. Out-of-order should not happen.
- If a tier's PR somehow lacks a merged dependency (shouldn't, given Phase 1's DAG-ordered execution): exit. Dispatcher re-fires; Phase 1 will recompute and retry.

## 5. Merge Conflicts During PR Auto-Merge

- Attempt automatic resolution for simple, well-known conflict patterns: barrel exports (`index.ts` re-export lists), registry additions (append-only arrays/objects), import lists at file tops.
- If a conflict is outside these patterns or auto-resolution fails:
  - Log affected files and the PR number to stdout.
  - Commit any safe partial work (typically nothing — the auto-merge step doesn't leave the worktree dirty).
  - Exit. The dispatcher's next tick re-fires; the worktree wipe clears any aborted merge state. The next invocation will retry the merge with origin's updated state.

## 6. Worktree Issues

- **Path already exists:** the worktree was created by a prior interrupted tick. The dispatcher's tick-start wipe operates on the **outer** worktree; nested per-slice worktrees survive. Check whether the existing slice worktree's branch matches what we want:
  - If yes: attach to it via `git worktree add <path> <branch>` (without `-b`).
  - If no: `git worktree remove --force <path>` then recreate. This is safe because per-slice worktrees only ever hold uncommitted slice-implementer output, which is recoverable.
- **Removal fails (uncommitted changes):** log and exit. The next tick will retry.
- **Stale references:** run `git worktree prune` at the end of a successful tier to clean up.

## 7. Branch Already Exists

- **Feature branch:** must exist (dispatcher's atomic rename created it). The precondition check verifies HEAD matches `feature/<feature>`; exit if not.
- **Slice branch already on origin:** auto-detect via `gh pr view <branch> --json state -q .state`:
  - `MERGED` → slice is done; skip in this invocation.
  - `OPEN` → PR was created but not yet merged; pick up at the Phase 4 auto-merge step.
  - No PR found → branch has commits but no PR was created. Continue: Phase 4 creates the PR, then merges it.
  - Branch with no commits past `feature/<feature>` HEAD → recreate the worktree on top.
- Never delete a slice branch automatically. Branches are evidence; preservation is intentional.

## 8. Push Fails

- Preconditions require a remote, so this means transient network / auth failure or remote rejection.
- Log and exit. The dispatcher's next tick will retry. There is no fallback to "local-only mode" — the harness model assumes remote is available.

## 9. Resuming After Interruption

- Every dispatcher tick wipes uncommitted state in the worktree (`git reset --hard HEAD && git clean -fd`) and re-invokes `/implement-mainspec`.
- The skill re-derives all state from disk on every invocation:
  - What's merged on `feature/<feature>` (Phase 1 idempotency check).
  - Which slice branches exist on origin and the state of their PRs (Phase 4 prep).
  - Which worktrees exist locally (Worktree Management section in SKILL.md).
- No checkpoint files or in-memory state to persist; the artifacts on disk ARE the state.

# Error Handling & Recovery

Reference for handling errors during mainspec implementation. Read this when any phase encounters errors.

## 1. Subagent Fails Implementation

- Log error details from subagent output
- Mark slice as failed in summary
- Other slices in the same tier are unaffected
- At tier gate, ask user: retry failed slice, skip it, or abort remaining tiers

## 2. Signal Validation Fails Inside Subagent

- The subagent handles this internally per implement-slice workflow (fix code, re-invoke signal, repeat)
- If the subagent ultimately gives up, it reports failure
- Orchestrator marks the slice as failed

## 3. PR Creation Fails

- Usually means branch wasn't pushed or remote is unavailable
- Log error, continue creating PRs for other slices
- User can manually create PR later: `gh pr create --head <branch> --base feat/<mainspec-name>`

## 4. Tier Gate — Dependency Not Merged

- Before starting a new tier, check if any required dependency PRs from the previous tier are still open (unmerged)
- If a blocking dependency is unmerged, warn user: "Slice X.Y depends on Slice W.Z (PR #N) which hasn't been merged yet. Merge it before proceeding, or skip Slice X.Y."

## 5. Merge Conflicts During PR Merge

- Attempt automatic resolution for simple conflicts (barrel exports, registry additions, import lists)
- If conflict is complex, report affected files to user and ask for guidance
- After resolution, continue merging remaining PRs

## 6. Worktree Issues

- **Path already exists:** `git worktree remove <path>` if safe, then recreate
- **Removal fails (uncommitted changes):** Warn user, skip cleanup. User can remove manually.
- **Stale references:** Run `git worktree prune` to clean up

## 7. Branch Already Exists

- **Feature branch:** `git checkout feat/<mainspec-name>`, resume from existing branch (check which slices are already committed)
- **Slice branch:** Ask user — reuse existing branch or delete and recreate

## 8. Push Fails

- No remote or auth issues: warn user, switch to local-only mode
- Local branches are preserved, PR creation is skipped

## 9. Resuming After Interruption

- Feature branch and slice branches persist on remote
- User can `/resume` the Claude Code session to continue from where it stopped
- All git state (branches, PRs) is preserved
- Orchestrator should check existing state before recreating branches/PRs

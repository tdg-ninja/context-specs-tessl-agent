# Release Strategy (Parallel Mode)

The feature branch IS the release candidate. PR `feat/<mainspec-name>` to `main` directly. No separate release branches.

## When to Release

The developer can release at any point during implementation:
- After Tier 0 (foundation only)
- After any tier's PRs are merged
- After all tiers are complete

The natural release unit is "everything merged to feat so far."

For partial release: leave unwanted slice PRs unmerged on feat, then PR feat to main with only the desired slices.

## How to Release

```bash
gh pr create --base main --head feat/<mainspec-name> \
  --title "Release: <mainspec-name>" \
  --body "Includes slices: <list merged slice numbers>"
```

## Lazy Merge Policy

After releasing (merging feat to main), do NOT immediately merge main back into feat. Only merge main into feat when:

1. Next release PR has merge conflicts with main
2. The feat branch needs changes that landed on main after the release

Git/GitHub handles the diff correctly — it knows what was already merged.

### If Merging main into feat for Conflict Resolution

```bash
git checkout feat/<mainspec-name>
git merge main
# Resolve any conflicts
# Run tests to verify nothing broke
git push origin feat/<mainspec-name>
# Then create the release PR
```

## Partial Release Constraints

The dependency DAG determines valid release subsets:
- Can't ship a slice without its dependencies (e.g., can't ship 3.6 without 3.2-3.5)
- Only merge slice PRs whose dependencies are also merged
- The summary report (Phase 6) lists valid release subsets

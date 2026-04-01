# Subagent Prompt Template

Use this template when spawning subagents for any tier (including Tier 0). Fill in the placeholder values for each slice.

## Template

```
You are implementing slice <number> (<name>) of the <mainspec-name> mainspec.

IMPORTANT: Your working directory is <working-directory-absolute-path>.
Before doing any work, run:
  cd <working-directory-absolute-path>

Read the slice file at:
  <absolute-spec-file-path>
  (This is an absolute path — it may be outside your working directory)

Follow the implement-slice workflow (preloaded in your context) to implement the slice.

Report your result:
  - SUCCESS: all code implemented, tests pass. List key files created/modified.
  - FAILURE: describe what went wrong and where you stopped

Do NOT run any git commands (add, commit, push) — the orchestrator handles git.
Do NOT create a PR — the orchestrator handles PR creation.
Do NOT modify files outside your assigned slice scope.
Do NOT use git worktree commands — you are already in the correct directory.
```

## Placeholder Reference

| Placeholder | Source | Example |
|------------|--------|---------|
| `<number>` | compute_tiers.py output → slice number | `3.3` |
| `<name>` | compute_tiers.py output → slice name | `BarChart Component` |
| `<mainspec-name>` | compute_tiers.py output → mainspec_name | `svg-and-charts` |
| `<working-directory-absolute-path>` | For Tier 0: repo root. For Tier 1+: `realpath .claude/worktrees/<mainspec>/<worktree>` | `/home/user/repo/.claude/worktrees/svg-and-charts/slice-3.3-barchart` |
| `<absolute-spec-file-path>` | compute_tiers.py output → slice file | `/home/user/specs/svg-and-charts/slices/3.3-barchart-component.md` |

## Usage

### Tier 0 (Sequential — foreground)

Spawn one subagent at a time. Wait for completion before spawning the next.

```python
Agent(
    subagent_type="slice-implementer",
    mode="bypassPermissions",
    name="slice-3.1",
    description="Implement slice 3.1",
    prompt="<filled template for slice 3.1>"
)
# Wait for completion
# Orchestrator runs: git add, git commit, git push
# Then spawn next Tier 0 slice
```

### Tier 1+ (Parallel — background)

Spawn all subagents for a tier in a **single message** for maximum parallelism:

```python
Agent(
    subagent_type="slice-implementer",
    run_in_background=True,
    mode="bypassPermissions",
    name="slice-3.2",
    description="Implement slice 3.2",
    prompt="<filled template for slice 3.2>"
)
Agent(
    subagent_type="slice-implementer",
    run_in_background=True,
    mode="bypassPermissions",
    name="slice-3.3",
    description="Implement slice 3.3",
    prompt="<filled template for slice 3.3>"
)
# ... one per slice in the tier
# Wait for all to complete
# Orchestrator handles git for each worktree
```

### Sequential Mode

Same as Tier 0 — spawn one at a time, foreground, orchestrator handles git after each.

```python
Agent(
    subagent_type="slice-implementer",
    mode="bypassPermissions",
    name="slice-1.1",
    description="Implement slice 1.1",
    prompt="<filled template for slice 1.1>"
)
# Wait for completion
# Orchestrator runs: git add, git commit
# Then spawn next slice
```

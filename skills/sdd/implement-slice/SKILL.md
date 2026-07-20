---
name: implement-slice
description: Implements a single slice with Signal validation and unit tests. Agent-first — invoked by the slice-implementer subagent (under implement-mainspec). No human-in-the-loop; signal validation iterates up to a bounded `max_signal_iterations` (default 3) before reporting FAILURE.
---

# Implement Slice

Executes a single slice with Signal validation and unit tests. Agent-first: invoked by the `slice-implementer` subagent in a worktree the parent orchestrator (`implement-mainspec`) has set up. No human prompts; bounded inner loop.

## Invocation Contract

This skill is invoked by the `slice-implementer` subagent, not directly by the harness dispatcher. The subagent's prompt provides:

**Inputs:**
- `slice_path` — absolute path to the slice file (may be outside the working directory).
- `working_directory` — absolute path to the worktree where work happens.
- `max_signal_iterations` — cap on the inner signal-fix-retry loop. Default: 3.

**Outputs (uncommitted, in the working directory):**
- Implemented code matching the slice's specification.
- Signal validation completed (passed or skipped per the slice's Signal section).
- Unit tests created/updated.

The parent orchestrator (`implement-mainspec`) handles git (add, commit, push) after this skill exits. Do NOT commit, do NOT run git operations, do NOT create PRs.

**Result reporting (to the calling subagent):**
- **SUCCESS**: list key files changed, signal status (passed | skipped), tests passing.
- **FAILURE**: describe what went wrong. Reasons include: `signal_failure` (cap hit), `test_failure` (unit tests red), `implementation_blocked` (spec contradicts the codebase).

## Workflow

1. **Read slice** - Load the entire slice file into context.
2. **Create TODO list** - Three items:
   - `{slice-name} - Implement`
   - `{slice-name} - Signal Validation`
   - `{slice-name} - Unit Tests`
3. **Implement** - Mark in_progress, implement all code specified in the slice.
4. **Signal validation** - Check the Signal section:
   - If Signal Skill specified: invoke `skill: "[signal-name]"`, wait for output.
   - Compare against Expected Behavior.
   - Fix issues and re-invoke. Track iterations.
   - If iterations reach `max_signal_iterations` (default 3) without success, return FAILURE with `reason: signal_failure` and the last signal output. Do not loop indefinitely.
   - If Signal Skill is "None": skip to unit tests.
5. **Unit tests** - Create/update unit tests for the implemented functionality.
6. **Complete** - Mark all TODOs complete, stop.

The working directory is set up freshly by `implement-mainspec` (a per-slice git worktree branched from `feature/<feature>`). There should be no prior partial state to resume from — work as if the slate is clean.

## Signal Processing

Each slice includes a Signal section after the Objective:

```markdown
## Signal

**Signal Skill:** [signal-skill-name | None]

**Expected Behavior:**
- What should succeed when correctly implemented
```

### Signal Workflow

1. After implementing slice code, check the Signal section
2. If Signal Skill is specified:
   - Invoke the signal: `skill: "[signal-name]"`
   - Wait for signal output
   - Follow the guidance from Signal
3. If signal indicates success: Continue to unit tests
4. If signal indicates failure:
   - Review signal output to identify specific issue
   - Fix the implementation
   - Re-invoke signal until success
5. If Signal Skill is "None": Skip to unit tests

## TODO Structure

```
[ ] 1.3-user-auth - Implement
[ ] 1.3-user-auth - Signal Validation
[ ] 1.3-user-auth - Unit Tests
```

## Guidelines

**DON'T:**
- Use `AskUserQuestion`. No human is in the loop.
- Implement beyond the slice scope.
- Proceed with failing signal validation — but also do not exceed `max_signal_iterations`; if the cap is hit, return FAILURE with `reason: signal_failure` and the last signal output.
- Skip signal validation if specified.
- Implement dependent slices (that's for implement-mainspec).
- Run git commands or create PRs — the parent orchestrator handles git.
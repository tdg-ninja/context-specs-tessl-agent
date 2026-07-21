---
name: implement-issue
description: Implement a structured GitHub issue in a repository and open a pull request. Use when a cloud or local agent is asked to read a GitHub issue, make the requested code or documentation change, run relevant checks, and create a PR that links the issue.
---

# Implement Issue

1. Read the issue number from the instructions and fetch it with `gh issue view`.
2. Validate the issue has Goal, Scope, Acceptance criteria, and Constraints; stop with a comment if it is not dispatchable.
3. Read the repo guidance files that exist (`AGENTS.md`, `CLAUDE.md`, README, and relevant docs); do not require files that are absent.
4. Create a branch named `agent/issue-<number>-<short-slug>` from the target base branch.
5. Make the smallest change that satisfies the issue, respecting its out-of-scope constraints.
6. Run relevant deterministic checks discovered from the repo; if checks are unavailable, report what was skipped and why.
7. Commit the change, push the branch, and open a PR that links or closes the issue.
8. In the PR body, separate Tessl actions from non-Tessl checks and mention any skipped checks or follow-up risks.

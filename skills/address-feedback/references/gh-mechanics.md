# GitHub mechanics (the plumbing)

The fiddly `gh` / GraphQL / REST commands the responder needs, kept out of the skill's
narrative. Commands are illustrative — adapt to the repo and your `gh` version. The skill
runs inside the feature worktree, so `gh` infers the PR from the current branch.

## 0. Reviewer identity (configure this first)

You act on **reviewer findings only** — never on human review comments. Which login the
reviewer posts under depends on the chosen reviewer:

- **Managed Anthropic Code Review** — posts as the Claude GitHub App (a `Bot`-type actor,
  e.g. login `claude[bot]` / `app/claude`). Confirm the exact login on a real PR in the repo.
- **Self-hosted `claude-code-action`** — posts under whatever identity the workflow uses
  (often `github-actions[bot]`, or a dedicated bot/PAT the project configured).

Treat the reviewer login as a **single configurable constant** at the top of your reasoning
(e.g. `REVIEWER_LOGIN`). Everything below filters to it. A comment whose author is not the
reviewer is a human's — leave it alone.

## 1. Find unresolved reviewer findings

Review **threads** carry the resolve-state; the REST review-comments endpoint carries bodies
and authors. The thread's `isResolved` is the truth for "still open" — the reviewer flips it to
resolved on its next pass once a Clear fix is pushed.

GraphQL gives both resolve-state and comments in one call:

```bash
gh api graphql -f query='
  query($owner:String!, $repo:String!, $pr:Int!) {
    repository(owner:$owner, name:$repo) {
      pullRequest(number:$pr) {
        reviewThreads(first:100) {
          nodes {
            id
            isResolved
            isOutdated
            comments(first:50) {
              nodes {
                databaseId
                body
                path
                line
                author { login }
              }
            }
          }
        }
      }
    }
  }' -f owner=OWNER -f repo=REPO -F pr=PR_NUMBER
```

Then, in your own reasoning, keep only threads where:
- `isResolved == false`, **and**
- the thread's **first** comment's `author.login == REVIEWER_LOGIN` (the finding is the
  reviewer's, not a human's).

The first comment is the finding; later comments in the thread are replies (possibly yours).

## 2. Idempotency checks (skip what you've handled)

Re-derived from the thread + git — no state file.

- **Reply-idempotency** (Ambiguous / Complex / Out-of-Scope): look at the thread's comments.
  If the **last** comment's `author.login` is **your** identity (the harness/responder login —
  the same identity your replies post under) and there's no newer reviewer comment after it,
  you've already answered → **skip this thread.**
- **Fix-idempotency** (Clear): before fixing, check whether the finding is already addressed —
  the current source already has the fix, or a recent commit (`git log --oneline -n 20`,
  `git log -p -- <path>`) already references/contains it. If so → **skip**; the reviewer just
  hasn't re-run yet. Re-deriving the problem from the worktree is the backstop: if there's no
  real problem, your fix produces no diff and you commit nothing.

## 3. Act

### Clear — fix, commit, push (no reply)
Edit the source so the cause is gone (scope-tight; obey the never-silence and skip rules).
Then:

```bash
git add -A
git commit -m "fix(review): <short description of the fix>"   # message references the finding
git push
```

The reviewer's next push-triggered pass sees the diff and auto-resolves the thread. **Post no
reply** — it would do nothing the reviewer reads. (This depends on the reviewer running in
"after every push" mode; that's the project's `REVIEW.md`/workflow setup, not yours.)

### Ambiguous / Complex / Out-of-Scope — reply in-thread (no code)
Add your reply to the **finding's existing thread** (so it threads under the comment, not as a
loose top-level comment) via the REST replies endpoint, keyed by the finding comment's
`databaseId` from step 1:

```bash
gh api -X POST \
  repos/OWNER/REPO/pulls/PR_NUMBER/comments/COMMENT_DATABASE_ID/replies \
  -f body='Excluded by the PRD'"'"'s Out of scope section — recommending a separate PRD.'
```

For **Complex**, include an `@`-mention of the human (the PR author or a configured owner) in
the body so they're pulled in for the architectural call.

## Notes
- **One reply per finding per invocation.** Reply-idempotency (step 2) prevents duplicates on
  later ticks.
- **Never** post a top-level PR comment for a finding response — replies thread under the
  finding so the conversation stays attached to the line. (`signal_stuck`, owned by the
  dispatcher, is the only thing that posts top-level.)
- If the GraphQL `reviewThreads` query isn't available for a given reviewer setup, fall back to
  `gh pr view --json reviews,comments` plus the REST `pulls/{n}/comments` list — but you lose
  the clean `isResolved` signal and must infer open-vs-addressed from the diff, which is
  weaker. Prefer the thread query.

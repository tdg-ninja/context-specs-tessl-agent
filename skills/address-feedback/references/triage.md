# Triage taxonomy (the hackable seam)

Every unresolved reviewer finding lands in **exactly one** of four buckets. This file is
the seam a project edits to retune classification without touching the skill's flow.

Two authorities govern every call:
- **PRD** (`prds/<feature>/prd.md`) — authoritative **scope**. Its `## Out of scope` section
  is decisive for the Out-of-PRD-Scope bucket.
- **Expert** (`.claude/skills/expert/`) — authoritative **patterns**. A Clear fix should
  match how this project already does things.

## The four buckets

| Bucket | What it means | Action | Reply? | Pushes code? |
|---|---|---|---|---|
| **Clear** | Unambiguous, in-scope, and you can fix the *cause* honestly within the finding's footprint. | Fix the cause, commit (message references the finding), push. | **No** — the diff is the signal; the reviewer auto-resolves on its next pass. | Yes |
| **Ambiguous** | In-scope, but you can't act without guessing intent. | Reply with the **specific** question that would unblock you. | Yes | No |
| **Complex** | A real, in-scope concern, but the honest fix needs an architectural call, changes behavior, or reveals the plan/spec is wrong. | Reply explaining the scope; **tag the human**. | Yes | No |
| **Out-of-PRD-Scope** | Asks for something the PRD's `## Out of scope` (or its silence on a non-goal) excludes. | Reply recommending a **separate PRD**. **Do not create a stub.** | Yes | No |

## Boundary heuristics (the judgment calls)

- **Clear vs Ambiguous.** Clear means the finding *and the project's patterns* point to one
  honest fix. If you'd have to pick between two plausible intents, it's Ambiguous — ask, don't
  guess. A wrong guess costs a whole review round; a question costs nothing.
- **Clear vs Complex.** If the only way to satisfy the finding is to **silence a check**, add a
  **skip marker**, weaken a config, refactor unrelated code, or change behavior the PRD pins —
  it is **not** Clear. Reply as Complex and escalate. "I *can* make the check green" is not the
  test; "the underlying problem is honestly gone, within this finding's footprint" is.
- **Complex vs Out-of-PRD-Scope.** Complex = in-scope but hard (needs a human's design call).
  Out-of-Scope = the PRD says we deliberately aren't doing this. Check the PRD's `## Out of
  scope` first; when a finding is a legitimate enhancement the PRD never claimed, it's
  Out-of-Scope, not Complex.
- **The "skip the flaky test" finding is always Complex.** Whether to skip a test is a human's
  call at STUCK, never the responder's. Reply escalating; never add the marker.
- **A `🟣 Pre-existing` finding** (the reviewer's marker for a bug not introduced by this PR) is
  Out-of-PRD-Scope by default — reply recommending a follow-up; don't expand this PR to fix
  unrelated pre-existing bugs.

## Worked examples

- *"This null check is missing — add one."* → **Clear.** Add the check, push, no reply.
- *"Should empty input be handled like the null case?"* → **Ambiguous.** Reply asking; the
  answer determines the fix.
- *"This would require restructuring the auth layer."* → **Complex.** Reply with the scope, tag
  the human.
- *"Pagination would help here."* when the PRD's `## Out of scope` lists pagination →
  **Out-of-PRD-Scope.** Reply recommending a separate PRD; build nothing.
- *"This test is flaky — just skip it."* → **Complex** (the skip rule). Reply escalating; never
  add `.skip`.

## Reply style (for the three reply buckets)

One reply per finding, in-thread, specific, and short. Name the bucket's reasoning in plain
language (e.g. "excluded by the PRD's Out of scope section — recommending a separate PRD").
Don't argue the reviewer down or try to suppress findings — convergence pressure lives in the
project's `REVIEW.md` (nit-suppression after the first review), not in your replies. Your reply
is a signal to the **human**, who will steer by pushing or merging.

# Chapter 6 — The mindset shift

*The payoff.*

Read the first five chapters and a single line falls out of them:

> **Your project is not a codebase you type into. It's a harness you tune.**

Read it literally: it describes what the previous chapters actually built. The
harness plans features, implements them,
verifies them, and remembers what it learns. The code is an *output* of the
system now — something the harness produces — not the thing you spend your hours
authoring.

The shift this asks of you is the hard part, because it's a shift in where you
put your attention.

## From syntax to context

The old craft was syntax: knowing the API, writing the loop, getting the types to
line up, remembering how this codebase does things. That craft is exactly the
**verifiable** work from Chapter 5 — the work the model is superhuman at. Keep
spending your attention there and you're racing a machine at the one game it
always wins.

The new craft is **context engineering** — the lever from Chapter 1, now wielded
deliberately and at every level:

- You shape the context the harness reasons over (the Expert, `AGENTS.md`, the
  specs).
- You decide what becomes a lint the agent can't ship past, and what stays
  flexible prose.
- You read the build trail to find where the context failed an agent, and you fix
  it so the next feature benefits.

When a feature comes out wrong, the question is no longer "let me go fix that
code." It's "what did the agent not know, and where should that knowledge live so
it never bites us again?" Fixing the code fixes one feature. Fixing the context
fixes the *class*.

## The three things that stay yours

Strip away the typing and what's left is the work that was always the most
valuable, now unobscured. Three things, and they are not going anywhere:

1. **Deep understanding of the problem space.** The harness can build anything you
   can specify; it cannot tell you what's worth specifying. That comes from your
   model of the domain — which is why the Understanding phase exists, and why it
   compounds (Chapter 5).
2. **Theorizing and expressing intent.** Deciding what to build, and pinning
   "done" to something executable. This is judgment under uncertainty — the part
   no exit code can hand you.
3. **Evaluating outcomes and improving the context.** Judging whether what got
   built is *right* in the ways a machine can't verify — and turning that judgment
   into better context, so every future feature inherits it.

Understand the problem. Express the intent. Evaluate the result and improve the
harness. That's the loop. The machine does the rest.

## Why it compounds

The reason this is worth the shift, and not just a rearrangement of chores: **the
system gets better the more you use it, and it gets better in a direction you
choose.**

Every merge can teach the Expert something. Every STUCK you resolve corrects a
piece of context for good. Every eval you capture freezes a behavior so a future
change can't silently regress it. A codebase you type into is a constant cost —
it decays, it needs maintenance, every feature starts roughly where the last one
did. A harness you tune is an *appreciating asset* — each feature leaves the
project a little more capable of building the next one.

That's the whole bet of Context Specs, stated plainly:

> Stop spending yourself on the work a model does better than you. Spend yourself
> on understanding, intent, and context — and let the project you've turned into
> a harness compound everything you put in.

---

That's the story. To go deeper on any layer, the chapters point into the actual
skills under [`skills/`](../skills/); to understand *why* the
harness is safe to leave running, read the **[design invariants](./invariants.md)**.

← [Back to the start](./README.md)

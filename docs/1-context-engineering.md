# Chapter 1 — Context engineering

> The single biggest lever you have when you build with a coding agent is what
> goes **into** — and what stays **out of** — its context window.

It helps to start with one observation, because everything else in this library
follows from it: an agent is only ever as good as the context it's reasoning
over — the actual set of tokens in its window at the moment it decides. Less the
model in the abstract than the material in front of it right now.

Everything Context Specs does is in service of getting the right context into
that window at the right time, and keeping everything else out.

## The window is the scarce resource

A coding agent doesn't "know" your codebase. At any instant it knows exactly
what's in its context window: the conversation so far, the files it has opened,
the tool output it has seen. That window is finite, and it degrades in ways that
are easy to forget:

- **Context decay.** In a long session, older messages lose influence. The agent
  pays the most attention to what's recent and quietly discounts what came
  before — so the careful plan you laid out twenty tool calls ago is no longer
  really steering anything.
- **Context pollution.** Left to roam, an agent retrieves context on its own:
  it greps, opens files, follows imports. A lot of what it pulls in is
  irrelevant, and every irrelevant token crowds out a relevant one.
- **Compaction loss.** When the window fills, the session is summarized to make
  room. You don't get to choose what's dropped. Critical details disappear and
  the agent "forgets" — not because it's careless, but because the bytes are
  gone.

None of these are quirks of a particular model; they're consequences of working
inside a finite window. And they intensify as a task grows — just when holding a
coherent picture matters most.

## Context engineering is choosing, not dumping

The intuitive move is to load everything up front: here's the whole architecture,
every convention, all the relevant files, now go. But that runs straight into the
three problems above — it front-loads the pollution and makes compaction a
near-certainty before the agent has done much of anything.

**Context engineering is the opposite discipline: the agent dynamically pulls
the context it needs, when it needs it, and the substrate it pulls from is the
filesystem.** Two techniques do most of the work:

- **Externalize the durable stuff.** Anything that must survive a long session —
  the plan, the conventions, the domain knowledge — lives in files on disk, not
  in the conversation. Files don't decay and don't get compacted. The agent
  re-reads them precisely when they're relevant.
- **Progressive disclosure.** You don't hand the agent dense detail; you hand it
  a *pointer* — a short, high-level description with a path. The agent reads the
  description first, decides whether it needs more, and only then opens the dense
  source. The window stays small and focused, holding just what the current step
  requires.

The filesystem is what makes this possible. A file is a unit of context the
agent can choose to load or ignore. A directory of well-named files is a menu it
can navigate just-in-time. The skill of context engineering is largely the skill
of *organizing that menu* — so the right thing is one obvious read away, and the
wrong thing is never accidentally in the window at all.

## Why this is the foundation

This lens carries through the whole library — the same idea, applied at larger
and larger scope:

- A **spec** is the plan, externalized so it can't decay or compact — and sliced
  so the agent only ever loads the piece it's working on. *(Chapter 2.)*
- An **Expert** is curated domain knowledge, pulled on demand instead of
  re-explained every session. *(Chapter 2.)*
- The **harness** runs a fresh context window per step, so no step ever inherits
  another's pollution — and grows a long-term memory so hard-won context
  survives across features. *(Chapters 3 and 4.)*
- The **human loop** is you, doing context engineering deliberately: deciding
  what the agents should have known, and putting it where they'll find it.
  *(Chapter 5.)*

It's one lever, pulled at every scale. Each layer is answering the same question:
*at this scope, what is the right context, and how does it reach the window at the
right moment?*

---

The first place that question gets a concrete answer is the oldest and most
familiar unit of work: a single feature. How do you give an agent exactly the
context it needs to build one thing well — and nothing it doesn't?

That's **Spec-Driven Development**, and it's where we go next.

→ [Chapter 2 — Spec-Driven Development](./2-spec-driven-development.md)

# Context Specs Best Practices

## When to Use Spec-Driven Development (SDD)

Use SDD when dealing with **larger intent** that requires:
- **2+ sprints** of work
- **Complex implementations** where planning and context curation add significant value
- Features that benefit from temporal ordering and phased delivery

For smaller, straightforward tasks (< 1 sprint), use **vibe coding** - traditional rapid development without formal spec planning.

---

## Who Should Run Spec Planning

**Senior developers should run spec planning.** Spec planning by definition is for larger, complex stories, and you want a senior developer leading this effort.

### Senior Leverage

When seniors curate context in a spec plan:
- **Other developers** (including junior developers) get to use the specs
- It's like having a senior peer programming with them throughout implementation
- The senior gets **tremendous leverage** - even though they might not implement the code themselves, they definitely **influenced the code** and **enabled their team**
- One senior can multiply their impact across multiple developers and features

---

## Spec Planning Output

Spec planning produces two key artifacts:

### Mainspec
- **Your end state** - what you're working backwards from
- Describes the complete feature when fully implemented
- Provides the "north star" for development

### Slices
- **Temporally ordered, chunk-size intents** (similar to user stories)
- Each slice is approximately 1 user story in scope
- Work backwards from the mainspec in logical, incremental steps
- Each slice can be implemented, tested, and deployed independently

---

## Benefits for Product Management

Spec planning helps product managers by:

### Grounded in Truth
- Plans are created from actual codebase(s), not guesswork
- Technical constraints are surfaced early
- Implementation details are realistic and achievable

### Predictable Story Creation
- **Slices become Jira user stories** (1 or more slices = 1 user story)
- Removes guesswork from story creation
- Stories are already technically validated before sprint planning

### Better Forecasting
- **More predictable epic sizing** - slices provide granular estimates
- **Improved forecasting** - temporal ordering reveals dependencies
- Reduces surprises during implementation

### Improved Communication
- **Specs are human-readable** - product managers can understand what tech is building
- Clear visibility into technical approach and trade-offs
- Better alignment between product vision and technical implementation

---

## Context Engineering Best Practices

Context Specs follow context engineering best practices to maximize AI agent effectiveness:

### 1. Planning Outside Agent's Context Window

**Problem**: Context decay - older messages get forgotten, ignored, or compacted during long-running agent sessions. Agents pay more attention to recent messages and treat older messages with less importance.

**Solution**: Keep your plan outside the agent's context window so it doesn't experience context decay.

**In SDD**: The spec-planning phase creates a spec plan in temporal order, persisted as external files. The coding agent reads these specs when needed, ensuring it always "pays attention" to the right context at the right time.

---

### 2. Progressive Disclosure

**Problem**: Loading all context upfront pollutes the context window with irrelevant details.

**Solution**: Use a two-part technique:
1. **Description with pointer** - Small, high-level description of context
2. **External dense context** - Detailed context that's only read when needed

The agent reads the description first. If it determines it needs the full context, only then does it read the external details.

**In SDD**: Spec files contain:
- End goal (mainspec) and chunk-size intents (slices)
- "Codebase context" including exact file paths, code snippets, Mermaid diagrams
- Clear WHAT and WHY for each intent

This structure allows agents to progressively discover the right context at the right time. For example, when the agent sees an exact file path in a spec, it reads that file only when performing that specific task. This keeps the context window focused and small.

---

### 3. Reduced Context Pollution

**Problem**: In agent mode, coding agents autonomously retrieve context from the codebase. This can lead to reading irrelevant context that pollutes the context window.

**Solution**: Provide curated context upfront so the agent doesn't need to randomly search.

**In SDD**: You give the spec to the coding agent with curated context. The agent doesn't have to search for files or context blindly - you've already provided relevant file paths, code patterns, and architectural context. This greatly reduces the risk of context pollution.

---

### 4. Protection Against Compaction

**Problem**: Context windows are finite. When the limit is reached, compaction summarizes message history to make room for new messages. You don't know what was dropped during compaction, which can cause the agent to "forget" critical details.

**Solution**: Persist important context in external files that can be re-read after compaction.

**In SDD**: Spec files persist context externally. Even if compaction happens, the newly compacted context window can read the spec file again to "remember" the right context. The plan doesn't get lost in compaction.

---

## Summary

Context Specs and Spec-Driven Development follow proven context engineering principles:
- **External persistence** prevents context decay and compaction loss
- **Progressive disclosure** keeps context windows focused
- **Curated context** reduces pollution from irrelevant code
- **Human-readable specs** improve cross-functional collaboration
- **Temporal ordering** enables predictable delivery

These practices make AI agents more effective and development more predictable.

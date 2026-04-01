# Context Specs

**Define domain knowledge once. It flows through planning, validation, and implementation automatically.**

Composable Agent Skills for spec-driven development designed to be extended with your organizations "Expert" knowledge.

---

What goes in or what stays out of your coding agents context window is the biggest lever you have as a developer when agentic coding.
Context Specs focuses on solving this problem.  Providing the right context and the right time.  All while, using your organization's expertise.


## How It Works

![Experts](./experts.png)

You create **domain experts** from your documentation using a single prompt with `/expert-sdd-creator`. Those experts automatically participate across the workflow: they inform spec planning with domain-specific context, validate specs through multi-agent consensus review, and provide runtime signal during implementation. 

Context Specs ships as a set of Agent Skills. Install once, invoke via slash commands.

---

## The Expert Composability Pattern

This is the core value proposition. Create an expert once, and it flows through three phases automatically:

1. **Create an expert** — Use `/expert-sdd-creator` with your domain documentation (framework docs, internal library guides, architecture patterns). It generates a complete expert directory: `SKILL.md` + `references/` + `scripts/`.

2. **That expert participates in Spec Planning** — When you run `/spec-planning`, the planner reads the expert catalog. If trigger keywords match your feature, the expert is auto-invoked to curate domain-specific context into the spec (framework patterns, DO/DON'T examples, type conventions).

3. **That expert participates in Spec Validation** — When you run `/spec-validate`, after multi-agent consensus, expert review runs as a dedicated phase. Relevant experts validate the spec for domain-specific anti-patterns, misuse, and gaps.

4. **That expert provides Signal during Implementation** — Each expert can include signal scripts that validate runtime behavior during `/implement-slice` and `/implement-mainspec`. The signal section in every slice references which expert signal to invoke.

**Composable**: Multiple experts activate for a single feature. A "React" expert and a "DynamoDB" expert both contribute when you're building a full-stack feature.

**Extensible**: Organizations add private experts for internal libraries, conventions, and patterns — without modifying any existing skills.

---

## Signal: The Dev-Code Feedback Loop

![Signal](./signal.png)

Signal is the runtime counterpart to expert guidance. Where experts curate context *before* implementation, signal validates behavior *during* implementation.

Every slice spec includes a Signal section that names a signal skill and expected behaviors. During implementation, after code is written, the agent invokes the signal — runs tests, calls endpoints, checks build output — and iterates until the signal validates success. This turns implementation from a single pass into a feedback loop where the agent knows if it's on track.

Unit tests are the default signal, but experts can define custom signals: deploy to a lower environment and check logs, run browser automation and take screenshots, call endpoints and validate responses. Each expert generates `run_signal.sh` + `signal-workflow.md` as part of its structure — Signal Mode is half of what an expert IS.

---

## Available Skills

Five built skills, in workflow order.

### Expert SDD Creator (`/expert-sdd-creator`)

Meta-skill: create domain experts from documentation in a single prompt.

**Input**: Path to a markdown file with domain knowledge + optional steering context (what to focus on, specific use cases).

**Output**: A complete expert directory:
```
expert-{name}/
├── SKILL.md                    # Expert Mode + Signal Mode
├── references/
│   ├── {topic-1}.md            # Synthesized from input docs
│   ├── {topic-N}.md
│   └── signal-workflow.md      # How signal validates behavior
└── scripts/
    ├── run_signal.sh           # Main signal execution
    └── {helper}.sh             # Additional helpers as needed
```

**Auto-registration**: Runs `validate_expert.sh` for structure compliance, then `register_expert.sh` to add entries to the `experts.md` and `signals.md` catalogs. Reports line numbers of insertions.

**Signal approach auto-detection**: Analyzes the domain to select the right signal strategy — test runners for testing frameworks, endpoint calls for APIs, build checks for build tools, schema validation for config, command parsing for CLI tools.

### Spec Planning (`/spec-planning`)

Turns user ideas into structured spec plans using Spec-Driven Development. Researches the codebase to ground specs in reality, asks clarifying questions, and writes temporal-ordered specs with clear dependencies.

**What it produces:**
- A mainspec (`/specs/<feature>/mainspec.md`) defining the complete end state
- Ordered slices (`/specs/<feature>/slices/`) — temporal chunks of intent, each focused on WHAT and WHY
- A Slice Dependency Map (table + Mermaid DAG) in every mainspec — the single source of truth for slice ordering
- A Signal section in every slice — how to validate the implementation at runtime

**Context engineering practices built into every spec:**
- **BEFORE/AFTER with precise file paths** — Show exact current state vs desired state, eliminating ambiguity
- **Type contracts first** — Define interfaces and schemas upfront; can be an entire slice focused only on types
- **DO/DON'T counterexamples** — One good example, one bad example with explanation of why the bad version fails
- **Narrative temporal flows with MermaidJS** — Sequence diagrams and flowcharts showing causality across system layers
- **Forward-looking requirements** — Each slice documents what future slices will need, preventing rework
- **BEFORE/AFTER directory structure** — Show structural changes with inline comments explaining what's new and why

**Expert integration**: Reads the expert catalog (`references/experts.md`) at the start of every planning session. Auto-invokes relevant experts when trigger keywords match.

### Spec Validate (`/spec-validate`)

Validates a mainspec and its slices using parallel subagent consensus, then expert review.

**Phase 1 — Multi-agent consensus**: Spawns 3+ parallel subagents (Opus) that independently review the spec. Each agent gets the same prompt and reviews independently. Consensus on issues indicates higher confidence:

| Consensus | Confidence | Interpretation |
|-----------|------------|----------------|
| 3/3 found | Very High | Definitely a real issue — prioritize fixing |
| 2/3 found | High | Likely a real issue — should fix |
| 1/3 found | Medium | Could be valid or false positive — use judgment |

**Phase 2 — Expert review**: After subagent results are collected, relevant `expert-*` skills are invoked for domain-specific validation — framework anti-patterns, internal library misuse, security concerns, infrastructure issues.

**Phase 3 — Consolidation**: Deduplicates findings across all subagents and expert review. Groups by consensus level. Presents a unified validation summary with prioritized recommendations.

### Implement Slice (`/implement-slice`)

Transforms a slice spec into a phased implementation plan, then implements it.

**Temporal phase ordering**: Adapts to the feature, but follows a natural layering:
1. **Types/Contracts** — Interfaces, schemas, data structures
2. **Domain Logic** — Core business logic and validation
3. **Persistence** — Database operations, queries, data access
4. **API Layer** — HTTP handlers, endpoints, request/response mapping
5. **UI Components** — Frontend components that consume the API

**Interactive**: Asks questions to clarify intent and validate assumptions before implementing. Presents the full phased plan for user approval.

**Cross-cutting concerns**: Every plan addresses observability (structured logs that prove behavior), idempotency and retry-safety, error handling patterns, and security considerations.

**Testing strategy**: Categorized test names (unit, integration) with specific test file paths — proves coverage without writing tests upfront.

**Signal processing**: After implementing code, checks the slice's Signal section. If a signal skill is specified, invokes it, follows guidance, and iterates until signal validates success.

### Implement Mainspec (`/implement-mainspec`)

Orchestrates implementation of an entire mainspec — all slices, in dependency order.

**Auto-detects execution mode:**
- **Sequential** (3 or fewer slices): Implements slices one at a time with direct commits to the current branch. Simple and linear.
- **Parallel** (more than 3 slices): Dependency-aware tiered execution with git worktree isolation, per-slice PRs, and tier gating.

**How parallel mode works:**
1. `compute_tiers.py` parses the Slice Dependency Map, performs topological sort, assigns slices to tiers
2. **Tier 0** (foundation): Implemented sequentially on the feature branch via `slice-implementer` subagents
3. **Subsequent tiers**: Git worktrees created per slice, `slice-implementer` subagents spawned in parallel (up to 7 concurrent), orchestrator handles all git operations
4. **Tier gating**: After each tier, PRs are created and presented for review. All PRs must merge before the next tier starts.

**Slice-implementer agent**: A focused subagent (`slice-implementer.md`) with `implement-slice` preloaded and `bypassPermissions` mode. It implements code; the orchestrator handles git.

**Signal invocation**: Each slice's signal is processed during implementation — the feedback loop runs per-slice, not just at the end.

---

## Design Philosophy

### Composable, Not Rigid

Experts are composed, not hardcoded. Add or remove experts without modifying existing skills. Multiple experts compose for a single feature — a React expert and a DynamoDB expert both contribute when building a full-stack feature. Organizations extend Context Specs with private experts for internal libraries and conventions.

### Why Temporal Slicing?

Features have a natural dependency order. Slicing by intent (WHAT needs to happen) rather than by component (frontend/backend) preserves this order. Each slice captures a coherent unit of work with clear dependencies on prior slices and clear contracts for future slices. The dependency DAG enables automatic parallelization — `compute_tiers.py` performs topological sort to identify which slices can run concurrently.

### Why Multi-Agent Validation?

A single reviewer has blind spots. Independent parallel review by 3+ Opus agents catches what any one reviewer would miss. Consensus scoring provides quantitative confidence (3/3 = very high, 2/3 = high, 1/3 = medium) rather than a binary pass/fail. Expert review adds a domain-specific layer on top of general-purpose validation.

### Context Engineering Built-In

Specs are designed around context engineering principles: planning happens outside the agent's context window (in structured documents), progressive disclosure feeds only the current slice to the implementation agent, and signal sections provide focused feedback without polluting the main context. See [Best Practices](./best-practices.md) for the full treatment of context engineering in spec-driven development.

---

## Project Structure

```
.claude/
  agents/
    slice-implementer.md          # Focused subagent for parallel execution
  skills/
    specs/
      spec-planning/              # Structured spec creation with expert integration
        SKILL.md
        references/
          experts.md              # Expert catalog
          signal.md               # Signal catalog
      spec-validate/              # Multi-agent consensus validation
        SKILL.md
      expert-sdd-creator/         # Meta-skill: create domain experts
        SKILL.md
        references/
          catalog-formats.md
          expert-structure.md
          signal-patterns.md
        scripts/
          register_expert.sh
          validate_expert.sh
    dev/
      implement-slice/            # Single slice implementation
        SKILL.md
      implement-mainspec/         # Full mainspec orchestration
        SKILL.md
        references/
          error-handling.md
          release-strategy.md
          subagent-prompt-template.md
        scripts/
          compute_tiers.py        # DAG parser + topological sort
          tests/
            test_tier_computation.py
    intent/                       # [Planned]
    qa/                           # [Planned]
    code-review/                  # [Planned]
    ops/                          # [Planned]
    feedback/                     # [Planned]
```

---

## Installation

Context Specs has two types of installable content — **skills** and **subagents** — each with its own installation step.

### Skills

```bash
npx skills add https://github.com/capitalone/context-specs
```

This installs all skills into your project's `.claude/skills/` directory.

### Subagents

```bash
curl -fsSL https://raw.githubusercontent.com/capitalone/context-specs/main/install-agents.sh | bash
```

Run from your target project directory. This copies agent definitions (e.g. `slice-implementer.md`) into `.claude/agents/`. Safe to re-run — existing agent files are updated to the latest version.


---

## Quick Start

**1. Create an expert** from your domain documentation:
```
/expert-sdd-creator
Docs: /path/to/your-framework-docs.md
Focus on: component patterns, testing conventions, common pitfalls
```

**2. Plan a feature** — the expert auto-activates when triggers match:
```
/spec-planning
```

**3. Validate the spec** — multi-agent consensus + expert review:
```
/spec-validate
```

**4. Implement** — sequential or parallel, based on slice count:
```
/implement-mainspec
```

---

## Vision: The Full SDLC Loop

The five built skills cover spec planning and development. The full vision is a continuous loop where specs flow through every SDLC phase:

![SDLC Flow](./sdlc.png)

**Intent** captures what to build. **Spec Planning** turns intent into structured specs. **Dev** implements specs with signal feedback. **Integration Tests** validate across service boundaries. **Code Review** verifies original intent is met. **Ops** uses specs to understand production changes. **Feedback** analyzes production data to generate new intent, completing the loop.

| Phase | Status | Skills |
|-------|--------|--------|
| Spec Planning | Built | `spec-planning`, `spec-validate`, `expert-sdd-creator` |
| Dev | Built | `implement-slice`, `implement-mainspec` |
| Intent | Planned | — |
| Integration Tests | Planned | — |
| Code Review | Planned | — |
| Ops | Planned | — |
| Feedback | Planned | — |

### Evals (Future)

Two levels of evaluation will measure and improve the SDLC:
- **SDLC-level evals**: Track metrics across all phases to identify bottlenecks and context loss
- **Phase-level evals**: Evaluate each skill independently — are specs comprehensive? Are implementations correct? Are reviews catching issues?

---

## Key Principles

| Principle | Description |
|-----------|-------------|
| Define Once, Use Everywhere | Experts and specs flow through planning, validation, and implementation |
| Composable, Not Rigid | Multiple experts activate per feature; add your own without modifying existing |
| Temporal Ordering | Slices ordered by dependency, enabling automatic parallelization |
| Consensus Over Binary | Multi-agent validation with confidence scoring |
| WHAT Not HOW | Specs define intent; implementation details left to dev phase |
| Signal-Driven Feedback | Runtime validation during implementation, not just after |

---

## Learn More

- [Best Practices](./best-practices.md) — When to use SDD, context engineering principles, senior leverage, PM benefits
- [Spec Planning Skill](./.claude/skills/specs/spec-planning/SKILL.md) — Full context engineering practices for spec creation
- [Spec Validate Skill](./.claude/skills/specs/spec-validate/SKILL.md) — Multi-agent consensus validation details
- [Expert SDD Creator Skill](./.claude/skills/specs/expert-sdd-creator/SKILL.md) — How experts are generated and registered
- [Implement Slice Skill](./.claude/skills/dev/implement-slice/SKILL.md) — Phased implementation planning
- [Implement Mainspec Skill](./.claude/skills/dev/implement-mainspec/SKILL.md) — Orchestration, tiers, and parallel execution

---

## License

MIT

---
name: spec-validate
description: Validate a spec, spec plan, or mainspec using multi-agent consensus. Use when a user asks to validate, review, or check a spec for problems before implementation.
---

# Spec Validate

Validate a mainspec and its slices using parallel foreground subagents for high-confidence issue detection.

## Pre-conditions

If mainspec path is not provided, ask user to provide it:
- "Which mainspec would you like me to validate? Please provide the path (e.g., `/specs/feature-name/mainspec.md`)"

---

## Phase 1: Spawn Foreground Validation Agents

Spawn 3 parallel subagents (or more if user specifies) to independently review the spec. Each agent gets the same prompt and reviews independently—consensus on issues indicates higher confidence. Only give file paths to the subagent. E.g. file path to mainspec.md, file path to slice-1.1, slice-1.2, etc.

### Spawn Agents in Foreground (Parallel)

Spawn all agents **in parallel in a single message** using the Task tool. Do **NOT** use `run_in_background`. All agents run concurrently and return summarized results automatically.

```
Task(
  description="Spec validation A",
  subagent_type="general-purpose",
  model="opus",
  prompt="[Validation prompt below with spec content inserted]"
)

Task(
  description="Spec validation B",
  subagent_type="general-purpose",
  model="opus",
  prompt="[Identical prompt]"
)

Task(
  description="Spec validation C",
  subagent_type="general-purpose",
  model="opus",
  prompt="[Identical prompt]"
)
```

All three agents execute concurrently and return summarized findings directly. No task IDs to track, no output files to read.

### Validation Prompt

Each agent receives this prompt (insert the actual spec content):

~~~
Do you see any flaw in this spec plan? Starting from the mainspec to its corresponding slices. Do you see any gap in logic or anything that was missed?
Ground your answers in the actual codebase referenced in the spec. 

## Spec to Validate

**Mainspec Path:** [path]

**Slices:**
[For each slice, insert file path to slice]

## Output Guidance
For each issue include: which slice/section, codebase file path / line numbers, what the problem is, and suggested fix if possible.
~~~

**Wait for all agents to return their summaries before proceeding.**

---

## Phase 2: Expert Review

After subagent results are collected, perform an expert validation pass. This happens after Phase 1 so you can focus expert review on areas the subagents flagged.

### Read the Spec Content

Read the mainspec and slice files to understand the spec content for expert consultation.

### Consult Relevant Experts

Expert skills are named `expert-*`. Based on the spec content, identify which experts apply and invoke them:

1. **Discover Available Experts** -  To discover available experts, use `ls .claude/skills/ | grep expert` (do not use Glob, as it may not resolve symlinks)
2. **Identify applicable experts** — Look at the spec content and determine which `expert-*` skills are relevant
3. **Invoke relevant experts** — Use `skill: "expert-*"` to get domain-specific validation guidance

### Expert-Informed Review

With expert context, review the spec for domain-specific issues:
- Framework-specific anti-patterns
- Internal library misuse
- Security concerns
- Infrastructure/deployment issues

**Collect expert findings** — Keep track of any issues identified during expert review. These will be merged with subagent findings in Phase 3.

---

## Phase 3: Consolidate All Results

After ALL work is complete (subagents + expert review), consolidate everything into one unified response.

### Deduplicate Issues

Two issues are "the same" if they:
- Reference the same slice/section AND
- Identify the same fundamental problem (even if worded differently)

Apply deduplication across:
- All 3 (or more) subagent findings
- Expert review findings

### Organize by Consensus

Group findings by how many agents identified them:

| Consensus | Confidence | Interpretation |
|-----------|------------|----------------|
| **3/3 found** | Very High | Definitely a real issue—prioritize fixing |
| **2/3 found** | High | Likely a real issue—should fix |
| **1/3 found** | Medium | Could be valid or false positive—use judgment |

Expert-only findings (not found by any subagent) should be included in "Other Findings" with a note that they came from expert review.

---

## Present Final Results

Combine everything into the final response:

```
## Validation Summary

[Brief overall assessment—is spec ready, needs work, or has major issues?]

## High Confidence Issues (Found by 3/3 agents)

[List deduplicated issues all agents agreed on]

## Medium Confidence Issues (Found by 2/3 agents)

[List deduplicated issues most agents found]

## Other Findings (Found by 1/3 agents)

[List unique findings from individual agents—note which agent found each]
[Include expert-only findings here with "[Expert Review]" tag]

## Recommendations

[Prioritized next steps]
```

---

## Notes

- **Default: 3 agents** — User can specify more (e.g., "use 5 agents") for critical specs
- **Model: opus** — Use opus for high-quality validation reasoning
- **Foreground parallel execution** — All subagents run concurrently in a single message and return summarized results directly, no background polling needed
- **No rigid output schema for agents** — Let them find issues naturally, then consolidate
- **Consensus = confidence** — Issues found by multiple independent agents are more likely real
- **Expert review after subagents** — Expert review runs after subagent results are in, allowing experts to focus on flagged areas
- **Single consolidation point** — All deduplication and merging happens once, after all work completes

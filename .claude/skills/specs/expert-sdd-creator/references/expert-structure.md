# Expert Structure Guide

Reference for creating well-structured SDD experts.

## Directory Layout

```
expert-{name}/
├── SKILL.md                    # Required: main entry point
├── references/                 # Required: domain knowledge
│   ├── {topic-1}.md
│   ├── {topic-N}.md
│   └── signal-workflow.md      # Required: signal documentation
└── scripts/                    # Required: signal scripts
    ├── run_signal.sh           # Required: main signal entry
    └── {helpers}.sh            # Optional: additional scripts
```

---

## SKILL.md Structure

### Frontmatter (YAML)

```yaml
---
name: expert-{name}
description: {domain} expertise with signal capability. {1-2 sentences about what it provides}. Use for {use cases}. Triggers: {comma-separated triggers} (project)
---
```

**Rules:**
- `name` must be `expert-` prefix + kebab-case name
- `description` must include triggers for auto-discovery
- `description` must end with `(project)`
- Triggers should be comprehensive but not overly broad

### Body Structure

```markdown
# {Expert Name}

{One-line description}

## Quick Reference

| Topic | Reference | Mode |
|-------|-----------|------|
| {topic} | `{file}.md` | Expert |
| Signal Workflow | `signal-workflow.md` | Signal |

---

## Expert Mode

**Use during:** Spec planning, learning, implementation guidance

### Quick Navigation

- **{Category}?** → `{file}.md` - {description}

---

## Signal Mode

**Use during:** Implementation phase (after spec exists)

### Quick Commands

| Action | Command |
|--------|---------|
| {action} | `scripts/{script}.sh {args}` |

→ See `references/signal-workflow.md` for detailed workflow
```

---

## Reference Files

### Organization Principles

1. **One topic per file** - keep files focused
2. **Practical over theoretical** - include examples
3. **Scannable structure** - use headers, tables, code blocks
4. **Link between files** - reference related content

### Required: signal-workflow.md

Every expert must have `references/signal-workflow.md` containing:

```markdown
# {Expert} Signal Workflow

**Use during:** Implementation phase
**NOT for:** Spec planning or general questions

## Workflow Overview

{Diagram or description of feedback loop}

## Signal Scripts

| Script | Purpose |
|--------|---------|
| `run_signal.sh` | {main purpose} |
| `{helper}.sh` | {purpose} |

## Script Usage

### {Script Name}

```bash
scripts/{script}.sh {args}
```

{Description of what it does}

## Interpreting Results

### Success
{What success looks like}

### Failure
{What failure looks like and how to fix}
```

---

## Scripts

### run_signal.sh Requirements

1. **Shebang**: `#!/bin/bash`
2. **Strict mode**: `set -euo pipefail`
3. **Usage info**: Show help when called incorrectly
4. **Structured output**: JSON or clearly formatted for AI parsing
5. **Exit codes**: 0=success, non-zero=failure

### Template Structure

```bash
#!/bin/bash
# run_signal.sh - {Expert} signal verification
#
# Usage: run_signal.sh <required-arg> [options]
#
# Options:
#   --option1 <value>    Description
#   --verbose            Show detailed output

set -euo pipefail

# Parse arguments
if [[ $# -lt 1 ]]; then
    echo "Usage: run_signal.sh <required-arg> [options]"
    exit 1
fi

# Main logic
{domain-specific checks}

# Output results
echo "{"
echo "  \"status\": \"$STATUS\","
echo "  \"details\": \"$DETAILS\""
echo "}"

exit $EXIT_CODE
```

---

## Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Expert directory | `expert-{domain}` | `expert-migrations` |
| Reference files | `{topic}.md` (kebab-case) | `rollback-strategies.md` |
| Signal workflow | `signal-workflow.md` | Always this name |
| Main signal script | `run_signal.sh` | Always this name |
| Helper scripts | `{verb}_{noun}.sh` | `parse_results.sh` |

---

## Common Patterns

### Expert for Testing Domain

```
expert-{test-framework}/
├── SKILL.md
├── references/
│   ├── test-patterns.md
│   ├── configuration.md
│   ├── troubleshooting.md
│   └── signal-workflow.md
└── scripts/
    ├── run_signal.sh        # Runs tests
    └── parse_results.sh     # Parses test output
```

### Expert for API/Service Domain

```
expert-{service}/
├── SKILL.md
├── references/
│   ├── endpoint-patterns.md
│   ├── authentication.md
│   ├── error-handling.md
│   └── signal-workflow.md
└── scripts/
    ├── run_signal.sh        # Calls endpoints
    └── check_health.sh      # Health checks
```

### Expert for Tool/CLI Domain

```
expert-{tool}/
├── SKILL.md
├── references/
│   ├── commands.md
│   ├── configuration.md
│   ├── best-practices.md
│   └── signal-workflow.md
└── scripts/
    ├── run_signal.sh        # Runs tool commands
    └── parse_output.sh      # Parses CLI output
```

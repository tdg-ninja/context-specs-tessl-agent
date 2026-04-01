---
name: expert-sdd-creator
description: Meta skill for creating new SDD experts from domain documentation. Provide a markdown file path with domain knowledge + optional steering context. Automatically synthesizes references, generates signal scripts, validates, and registers in experts.md/signals.md catalogs. Single-prompt creation with follow-up tweaks. Triggers: create expert, new expert, make expert, expert for, domain expert, add expert (project)
---

# Expert SDD Creator

Create SDD experts from domain documentation in a single prompt.

## Required Input

1. **Domain docs** (required): Path to markdown file with domain knowledge
2. **Steering** (optional but recommended): What to focus on, specific use cases

Example prompt:
```
Create an expert for my custom testing framework.
Docs: /path/to/custom-docs.md
Focus on: component testing, live dependency testing, Cucumber BDD patterns
```

---

## Creation Process

### 1. Analyze Input

Read the markdown file and steering context to determine:
- Expert name (kebab-case, prefixed with `expert-`)
- Triggers (keywords that invoke this expert)
- Key topics for reference files
- Signal validation approach

### 2. Generate Expert Structure

Create directory at `.claude/skills/expert-{name}/` (sibling to this skill's directory):

```
expert-{name}/
├── SKILL.md                    # Frontmatter + Expert Mode + Signal Mode
├── references/
│   ├── {topic-1}.md            # Synthesized from input docs
│   ├── {topic-N}.md
│   └── signal-workflow.md      # How signal validates behavior
└── scripts/
    ├── run_signal.sh           # Main signal execution
    └── {helper}.sh             # Additional helpers as needed
```

### 3. Synthesize References

From the input markdown:
- Extract key topics and organize into separate reference files
- Keep each file focused on one topic
- Include practical examples and patterns
- Create `signal-workflow.md` describing validation approach

### 4. Generate Signal Scripts

Analyze domain to determine appropriate signal approach:

| Domain Type | Signal Approach |
|-------------|-----------------|
| Testing (Cucumber, JUnit) | Run tests, parse results |
| API/Service (REST, GraphQL) | Call endpoints, check responses |
| Build/Deploy (Maven, Gradle) | Run build, check artifacts |
| Config/Data (YAML, JSON) | Validate syntax, check schema |
| CLI tools (flyway, kubectl) | Run commands, parse output |

Generate `run_signal.sh` with domain-specific checks and TODOs for customization.

### 5. Write SKILL.md

Structure the expert's SKILL.md:

```yaml
---
name: expert-{name}
description: {domain} expertise with signal capability. {what it provides}. Triggers: {trigger-list} (project)
---
```

Body includes:
- **Expert Mode**: Quick reference table, navigation to references
- **Signal Mode**: Quick commands, reference to signal-workflow.md

### 6. Validate & Register

Run validation:
```bash
scripts/validate_expert.sh /path/to/expert-{name}
```

If valid, register:
```bash
scripts/register_expert.sh /path/to/expert-{name}
```

### 7. Report Results

Output to user:
- Created directory structure
- List of synthesized reference files
- Signal approach explanation
- Registration locations (line numbers in experts.md/signals.md)
- Path to expert for tweaking
- Any clarifying questions about signal scripts

---

## Expert Structure Requirements

Every expert must have:

1. **SKILL.md** with valid YAML frontmatter:
   - `name`: expert-{name} format
   - `description`: includes triggers and "(project)" suffix

2. **references/** directory with:
   - At least one domain knowledge file
   - `signal-workflow.md` describing validation approach

3. **scripts/** directory with:
   - `run_signal.sh` (executable)
   - Helper scripts as needed

→ See `references/expert-structure.md` for detailed patterns

---

## Signal Mode

Validate and register created experts.

### Quick Commands

| Action | Command |
|--------|---------|
| Validate | `scripts/validate_expert.sh <expert-dir>` |
| Register | `scripts/register_expert.sh <expert-dir>` |

### Validation Checks

- Directory structure complete (SKILL.md, references/, scripts/)
- YAML frontmatter valid (name, description)
- references/ contains files
- scripts/run_signal.sh exists and is executable
- signal-workflow.md present

### Registration

- Parses expert metadata from SKILL.md
- Generates entries for experts.md and signals.md
- Inserts at end of Expert Entries / Signal Entries section
- Reports line numbers of insertions

→ See `references/catalog-formats.md` for entry formats
→ See `references/signal-patterns.md` for signal script patterns

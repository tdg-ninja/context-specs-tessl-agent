# Catalog Entry Formats

Formats for registering experts in `experts.md` and `signals.md` catalogs.

Location of catalogs (sibling to this skill's install directory):
- `.claude/skills/spec-planning/references/experts.md`
- `.claude/skills/spec-planning/references/signals.md`

---

## experts.md Entry Format

Add under `## Expert Entries` section:

```markdown
### N. {expert-name}

**Description:** {2-3 sentence description of what the expert provides}

**Triggers:**
- {trigger-1}
- {trigger-2}
- {trigger-N}

**What It Provides:**
- {capability-1}
- {capability-2}
- {capability-N}

**Signal Capability:**
- {signal-validation-1}
- {signal-validation-N}

**Skill Name:** `{expert-name}`

---
```

### Field Details

| Field | Description |
|-------|-------------|
| N | Sequential number (next after last entry) |
| expert-name | Matches `name` from SKILL.md frontmatter |
| Description | Domain expertise summary + signal capability mention |
| Triggers | Keywords that invoke this expert (from frontmatter) |
| What It Provides | Expert mode capabilities (from references) |
| Signal Capability | What signal mode validates |
| Skill Name | Exact skill name for invocation |

### Example Entry

```markdown
### 4. expert-migrations

**Description:** Database migration expertise for Flyway and Liquibase. Provides schema versioning patterns, rollback strategies, and CI/CD integration guidance. Includes signal capability for migration status validation.

**Triggers:**
- Flyway, Liquibase, database migrations
- Schema versioning, DDL changes
- Rollback, migration status
- Signal, verify migrations

**What It Provides:**
- Migration file naming and versioning conventions
- Rollback strategy patterns
- CI/CD pipeline integration
- Troubleshooting common migration failures

**Signal Capability:**
- Migration status check (pending, applied, failed)
- Schema validation
- Rollback verification

**Skill Name:** `expert-migrations`

---
```

---

## signals.md Entry Format

Add under `## Signal Entries` section:

```markdown
### N. {expert-name} (with signal capability)

**Description:** {1 sentence describing what the signal validates}

**Triggers:**
- {signal-trigger-1}
- {signal-trigger-2}
- {signal-trigger-N}

**What It Validates:**
- {validation-1}
- {validation-2}
- {validation-N}

**How to Invoke:** `skill: "{expert-name}"`

**Typical Expected Behaviors:**
- {expected-behavior-1}
- {expected-behavior-2}
- {expected-behavior-N}

**Typical Failure Indicators:**
- {failure-indicator-1}
- {failure-indicator-2}
- {failure-indicator-N}

**Skill Name:** `{expert-name}`

---
```

### Field Details

| Field | Description |
|-------|-------------|
| N | Sequential number (next after last entry) |
| expert-name | Matches `name` from SKILL.md frontmatter |
| Description | What signal mode validates (1 sentence) |
| Triggers | Keywords that invoke signal mode |
| What It Validates | Specific validations performed |
| How to Invoke | Skill invocation syntax |
| Expected Behaviors | What success looks like |
| Failure Indicators | What failure looks like |

### Example Entry

```markdown
### 4. expert-migrations (with signal capability)

**Description:** Runtime validation for database migration status and schema consistency.

**Triggers:**
- Check migration status, verify migrations
- Run flyway info, liquibase status
- Signal, migration validation

**What It Validates:**
- Migration execution status (pending, applied, failed)
- Schema version consistency
- Rollback capability verification

**How to Invoke:** `skill: "expert-migrations"`

**Typical Expected Behaviors:**
- All migrations show "applied" status
- Schema version matches expected version
- No pending migrations in production

**Typical Failure Indicators:**
- Migrations show "pending" or "failed" status
- Schema version mismatch
- Connection errors to database
- Checksum validation failures

**Skill Name:** `expert-migrations`

---
```

---

## Insertion Rules

1. **Position**: Add after the last `### N.` entry in each file
2. **Numbering**: Increment N from the last entry
3. **Separator**: Include `---` after each entry
4. **Both files**: Always update both experts.md AND signals.md

---

## Extraction from SKILL.md

The `register_expert.sh` script extracts:

| Catalog Field | Source |
|---------------|--------|
| expert-name | `name` from frontmatter |
| Description | `description` from frontmatter (truncated/adapted) |
| Triggers | Parsed from `description` after "Triggers:" |
| What It Provides | Derived from reference file names |
| Signal Capability | Derived from signal-workflow.md |
| Expected Behaviors | From signal-workflow.md "Success" section |
| Failure Indicators | From signal-workflow.md "Failure" section |

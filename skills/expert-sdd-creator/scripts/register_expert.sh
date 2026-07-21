#!/bin/bash
# register_expert.sh - Register expert in experts.md and signals.md catalogs
#
# Usage: register_expert.sh <expert-dir> [--dry-run]
#
# Parses expert metadata from SKILL.md and inserts entries into:
#   - .claude/skills/spec-planning/references/experts.md  (resolved via SKILLS_BASE)
#   - .claude/skills/spec-planning/references/signals.md  (resolved via SKILLS_BASE)
#
# Exit codes:
#   0 = Success
#   1 = Error

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

if [[ $# -lt 1 ]]; then
    echo "Usage: register_expert.sh <expert-dir> [--dry-run]"
    exit 1
fi

EXPERT_DIR="$1"
DRY_RUN=false

if [[ "${2:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Derive skills base from script location.
# Script is at: .claude/skills/expert-sdd-creator/scripts/register_expert.sh
# Skills base (.claude/skills/) is 2 directories up from SCRIPT_DIR.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_BASE="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ ! -d "$SKILLS_BASE/spec-planning" ]]; then
    echo -e "${RED}ERROR:${NC} Could not locate spec-planning skill."
    echo "  Expected at: $SKILLS_BASE/spec-planning/"
    echo "  Install it with: npx skills add <spec-planning-repo>"
    exit 1
fi

EXPERTS_MD="$SKILLS_BASE/spec-planning/references/experts.md"
SIGNALS_MD="$SKILLS_BASE/spec-planning/references/signals.md"

echo "═══════════════════════════════════════════════════════════════"
echo "EXPERT REGISTRATION"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Expert directory: $EXPERT_DIR"
echo "Experts catalog:  $EXPERTS_MD"
echo "Signals catalog:  $SIGNALS_MD"
if $DRY_RUN; then
    echo -e "${YELLOW}Mode: DRY RUN (no changes will be made)${NC}"
fi
echo ""

# Check expert directory exists
if [[ ! -d "$EXPERT_DIR" ]]; then
    echo -e "${RED}ERROR:${NC} Expert directory not found: $EXPERT_DIR"
    exit 1
fi

# Check SKILL.md exists
if [[ ! -f "$EXPERT_DIR/SKILL.md" ]]; then
    echo -e "${RED}ERROR:${NC} SKILL.md not found in $EXPERT_DIR"
    exit 1
fi

# Check catalog files exist
if [[ ! -f "$EXPERTS_MD" ]]; then
    echo -e "${RED}ERROR:${NC} Experts catalog not found: $EXPERTS_MD"
    exit 1
fi
if [[ ! -f "$SIGNALS_MD" ]]; then
    echo -e "${RED}ERROR:${NC} Signals catalog not found: $SIGNALS_MD"
    exit 1
fi

# Parse SKILL.md frontmatter
echo "Parsing SKILL.md..."

# Extract frontmatter
FRONTMATTER=$(sed -n '/^---$/,/^---$/p' "$EXPERT_DIR/SKILL.md" | sed '1d;$d')

# Extract name
EXPERT_NAME=$(echo "$FRONTMATTER" | grep "^name:" | sed 's/name: *//')
if [[ -z "$EXPERT_NAME" ]]; then
    echo -e "${RED}ERROR:${NC} Could not extract 'name' from frontmatter"
    exit 1
fi

# Extract description
DESCRIPTION=$(echo "$FRONTMATTER" | grep "^description:" | sed 's/description: *//')
if [[ -z "$DESCRIPTION" ]]; then
    echo -e "${RED}ERROR:${NC} Could not extract 'description' from frontmatter"
    exit 1
fi

# Extract triggers from description (after "Triggers:")
TRIGGERS=""
if echo "$DESCRIPTION" | grep -q "Triggers:"; then
    TRIGGERS=$(echo "$DESCRIPTION" | sed 's/.*Triggers: *//' | sed 's/ *(project).*//')
fi

echo "  Name: $EXPERT_NAME"
echo "  Description: ${DESCRIPTION:0:60}..."
echo "  Triggers: ${TRIGGERS:0:60}..."
echo ""

# Check if expert already registered
if grep -q "### [0-9]*\. $EXPERT_NAME$" "$EXPERTS_MD"; then
    echo -e "${YELLOW}WARNING:${NC} Expert '$EXPERT_NAME' already exists in experts.md"
    echo "Skipping registration to avoid duplicates."
    exit 0
fi

# Count existing entries to determine next number
LAST_NUM=$(grep '### [0-9]*\.' "$EXPERTS_MD" | sed 's/### \([0-9]*\)\..*/\1/' | tail -1)
if [[ -z "$LAST_NUM" ]]; then
    LAST_NUM=0
fi
NEXT_NUM=$((LAST_NUM + 1))

echo "Next entry number: $NEXT_NUM"
echo ""

# Get reference files for "What It Provides"
PROVIDES=""
if [[ -d "$EXPERT_DIR/references" ]]; then
    for ref in "$EXPERT_DIR/references"/*.md; do
        if [[ -f "$ref" && "$(basename "$ref")" != "signal-workflow.md" ]]; then
            # Convert filename to readable form
            TOPIC=$(basename "$ref" .md | tr '-' ' ' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) substr($i,2)}1')
            PROVIDES="${PROVIDES}- ${TOPIC} guidance\n"
        fi
    done
fi

# Generate experts.md entry
read -r -d '' EXPERTS_ENTRY << EOF || true

### ${NEXT_NUM}. ${EXPERT_NAME}

**Description:** ${DESCRIPTION%% Triggers:*}

**Triggers:**
$(echo "$TRIGGERS" | tr ',' '\n' | sed 's/^ */- /')

**What It Provides:**
$(echo -e "$PROVIDES")
**Signal Capability:**
- Runtime validation (see signal-workflow.md)

**Skill Name:** \`${EXPERT_NAME}\`

---
EOF

# Generate signals.md entry
read -r -d '' SIGNALS_ENTRY << EOF || true

### ${NEXT_NUM}. ${EXPERT_NAME} (with signal capability)

**Description:** Runtime validation for ${EXPERT_NAME#expert-} domain

**Triggers:**
$(echo "$TRIGGERS" | tr ',' '\n' | sed 's/^ */- /')
- signal, verify, validate

**What It Validates:**
- Domain-specific behavior validation
- See references/signal-workflow.md for details

**How to Invoke:** \`skill: "${EXPERT_NAME}"\`

**Typical Expected Behaviors:**
- Signal scripts return exit code 0
- Validation checks pass

**Typical Failure Indicators:**
- Signal scripts return non-zero exit code
- Validation errors in output

**Skill Name:** \`${EXPERT_NAME}\`

---
EOF

echo "═══════════════════════════════════════════════════════════════"
echo "ENTRIES TO ADD"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}experts.md entry:${NC}"
echo "$EXPERTS_ENTRY"
echo ""
echo -e "${BLUE}signals.md entry:${NC}"
echo "$SIGNALS_ENTRY"
echo ""

if $DRY_RUN; then
    echo "═══════════════════════════════════════════════════════════════"
    echo -e "${YELLOW}DRY RUN - No changes made${NC}"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "To apply changes, run without --dry-run flag"
    exit 0
fi

# Find insertion point in experts.md (before "## Example:")
echo "Inserting into experts.md..."
# Find line number of "## Example:" section
EXPERTS_INSERT_LINE=$(grep -n "^## Example:" "$EXPERTS_MD" | head -1 | cut -d: -f1)
if [[ -z "$EXPERTS_INSERT_LINE" ]]; then
    # If no Example section, append to end
    echo "$EXPERTS_ENTRY" >> "$EXPERTS_MD"
    EXPERTS_INSERT_LINE="end"
else
    # Insert before Example section
    EXPERTS_INSERT_LINE=$((EXPERTS_INSERT_LINE - 1))
    # Create temp file with insertion
    head -n "$EXPERTS_INSERT_LINE" "$EXPERTS_MD" > "$EXPERTS_MD.tmp"
    echo "$EXPERTS_ENTRY" >> "$EXPERTS_MD.tmp"
    tail -n +"$((EXPERTS_INSERT_LINE + 1))" "$EXPERTS_MD" >> "$EXPERTS_MD.tmp"
    mv "$EXPERTS_MD.tmp" "$EXPERTS_MD"
fi
echo -e "  ${GREEN}Done${NC} (inserted at line $EXPERTS_INSERT_LINE)"

# Find insertion point in signals.md (before "## How to Use")
echo "Inserting into signals.md..."
SIGNALS_INSERT_LINE=$(grep -n "^## How to Use" "$SIGNALS_MD" | head -1 | cut -d: -f1)
if [[ -z "$SIGNALS_INSERT_LINE" ]]; then
    # If no How to Use section, append to end
    echo "$SIGNALS_ENTRY" >> "$SIGNALS_MD"
    SIGNALS_INSERT_LINE="end"
else
    # Insert before How to Use section
    SIGNALS_INSERT_LINE=$((SIGNALS_INSERT_LINE - 1))
    # Create temp file with insertion
    head -n "$SIGNALS_INSERT_LINE" "$SIGNALS_MD" > "$SIGNALS_MD.tmp"
    echo "$SIGNALS_ENTRY" >> "$SIGNALS_MD.tmp"
    tail -n +"$((SIGNALS_INSERT_LINE + 1))" "$SIGNALS_MD" >> "$SIGNALS_MD.tmp"
    mv "$SIGNALS_MD.tmp" "$SIGNALS_MD"
fi
echo -e "  ${GREEN}Done${NC} (inserted at line $SIGNALS_INSERT_LINE)"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}REGISTRATION COMPLETE${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "{"
echo "  \"expert\": \"$EXPERT_NAME\","
echo "  \"status\": \"REGISTERED\","
echo "  \"experts_md_line\": \"$EXPERTS_INSERT_LINE\","
echo "  \"signals_md_line\": \"$SIGNALS_INSERT_LINE\""
echo "}"

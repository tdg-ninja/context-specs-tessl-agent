#!/bin/bash
# validate_expert.sh - Validate expert directory structure
#
# Usage: validate_expert.sh <expert-dir>
#
# Validates:
#   - Directory structure (SKILL.md, references/, scripts/)
#   - YAML frontmatter (name, description)
#   - References directory has files
#   - signal-workflow.md exists
#   - scripts/run_signal.sh exists and is executable
#
# Exit codes:
#   0 = Valid
#   1 = Invalid

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [[ $# -lt 1 ]]; then
    echo "Usage: validate_expert.sh <expert-dir>"
    exit 1
fi

EXPERT_DIR="$1"
ERRORS=0
WARNINGS=0

echo "═══════════════════════════════════════════════════════════════"
echo "EXPERT VALIDATION"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Directory: $EXPERT_DIR"
echo ""

# Check directory exists
if [[ ! -d "$EXPERT_DIR" ]]; then
    echo -e "${RED}[FAIL]${NC} Directory does not exist: $EXPERT_DIR"
    exit 1
fi

# Extract expert name from directory
EXPERT_NAME=$(basename "$EXPERT_DIR")

echo "Validating: $EXPERT_NAME"
echo ""

# 1. Check SKILL.md exists
echo -n "[1/7] SKILL.md exists: "
if [[ -f "$EXPERT_DIR/SKILL.md" ]]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC}"
    ((ERRORS++))
fi

# 2. Check YAML frontmatter
echo -n "[2/7] Valid YAML frontmatter: "
if [[ -f "$EXPERT_DIR/SKILL.md" ]]; then
    # Extract frontmatter (between --- markers)
    FRONTMATTER=$(sed -n '/^---$/,/^---$/p' "$EXPERT_DIR/SKILL.md" | sed '1d;$d')

    # Check for name field
    if echo "$FRONTMATTER" | grep -q "^name:"; then
        # Check for description field
        if echo "$FRONTMATTER" | grep -q "^description:"; then
            echo -e "${GREEN}PASS${NC}"
        else
            echo -e "${RED}FAIL${NC} - missing 'description' field"
            ((ERRORS++))
        fi
    else
        echo -e "${RED}FAIL${NC} - missing 'name' field"
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}SKIP${NC} - SKILL.md not found"
fi

# 3. Check name matches directory
echo -n "[3/7] Name matches directory: "
if [[ -f "$EXPERT_DIR/SKILL.md" ]]; then
    SKILL_NAME=$(sed -n '/^---$/,/^---$/p' "$EXPERT_DIR/SKILL.md" | grep "^name:" | sed 's/name: *//')
    if [[ "$SKILL_NAME" == "$EXPERT_NAME" ]]; then
        echo -e "${GREEN}PASS${NC}"
    else
        echo -e "${YELLOW}WARN${NC} - name '$SKILL_NAME' != directory '$EXPERT_NAME'"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}SKIP${NC}"
fi

# 4. Check references/ directory
echo -n "[4/7] references/ directory: "
if [[ -d "$EXPERT_DIR/references" ]]; then
    REF_COUNT=$(find "$EXPERT_DIR/references" -name "*.md" -type f | wc -l | tr -d ' ')
    if [[ $REF_COUNT -gt 0 ]]; then
        echo -e "${GREEN}PASS${NC} ($REF_COUNT files)"
    else
        echo -e "${RED}FAIL${NC} - no .md files in references/"
        ((ERRORS++))
    fi
else
    echo -e "${RED}FAIL${NC} - directory not found"
    ((ERRORS++))
fi

# 5. Check signal-workflow.md exists
echo -n "[5/7] signal-workflow.md: "
if [[ -f "$EXPERT_DIR/references/signal-workflow.md" ]]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - not found"
    ((ERRORS++))
fi

# 6. Check scripts/ directory
echo -n "[6/7] scripts/ directory: "
if [[ -d "$EXPERT_DIR/scripts" ]]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} - directory not found"
    ((ERRORS++))
fi

# 7. Check for executable signal scripts
echo -n "[7/7] Signal scripts: "
if [[ -d "$EXPERT_DIR/scripts" ]]; then
    # Look for run_signal.sh or any *signal*.sh script
    SIGNAL_SCRIPTS=$(find "$EXPERT_DIR/scripts" -name "*.sh" -type f \( -name "run_signal.sh" -o -name "*signal*.sh" \) 2>/dev/null || true)
    if [[ -n "$SIGNAL_SCRIPTS" ]]; then
        SCRIPT_NAME=$(basename "$(echo "$SIGNAL_SCRIPTS" | head -1)")
        # Check if at least one is executable
        EXECUTABLE_COUNT=0
        for script in $SIGNAL_SCRIPTS; do
            if [[ -x "$script" ]]; then
                ((EXECUTABLE_COUNT++))
            fi
        done
        if [[ $EXECUTABLE_COUNT -gt 0 ]]; then
            echo -e "${GREEN}PASS${NC} ($SCRIPT_NAME)"
        else
            echo -e "${YELLOW}WARN${NC} - found but not executable"
            ((WARNINGS++))
        fi
    else
        # Fallback: check for any .sh scripts
        ANY_SCRIPTS=$(find "$EXPERT_DIR/scripts" -name "*.sh" -type f 2>/dev/null | head -1 || true)
        if [[ -n "$ANY_SCRIPTS" ]]; then
            SCRIPT_NAME=$(basename "$ANY_SCRIPTS")
            echo -e "${YELLOW}WARN${NC} - found $SCRIPT_NAME (not named *signal*)"
            ((WARNINGS++))
        else
            echo -e "${RED}FAIL${NC} - no .sh scripts found"
            ((ERRORS++))
        fi
    fi
else
    echo -e "${RED}FAIL${NC} - scripts/ not found"
    ((ERRORS++))
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "SUMMARY"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if [[ $ERRORS -eq 0 ]]; then
    echo -e "${GREEN}VALID${NC} - Expert structure is valid"
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}$WARNINGS warning(s)${NC}"
    fi
    echo ""
    echo "{"
    echo "  \"expert\": \"$EXPERT_NAME\","
    echo "  \"status\": \"VALID\","
    echo "  \"errors\": $ERRORS,"
    echo "  \"warnings\": $WARNINGS"
    echo "}"
    exit 0
else
    echo -e "${RED}INVALID${NC} - $ERRORS error(s) found"
    if [[ $WARNINGS -gt 0 ]]; then
        echo -e "${YELLOW}$WARNINGS warning(s)${NC}"
    fi
    echo ""
    echo "{"
    echo "  \"expert\": \"$EXPERT_NAME\","
    echo "  \"status\": \"INVALID\","
    echo "  \"errors\": $ERRORS,"
    echo "  \"warnings\": $WARNINGS"
    echo "}"
    exit 1
fi

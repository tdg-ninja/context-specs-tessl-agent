# Signal Script Patterns

Common patterns for generating signal scripts based on domain type.

---

## Pattern Selection

| Domain Keywords | Pattern | Primary Check |
|-----------------|---------|---------------|
| test, cucumber, junit, karate | Testing | Run tests, parse results |
| api, rest, endpoint, http, graphql | API/Service | Call endpoints, check responses |
| build, maven, gradle, npm | Build | Run build, check artifacts |
| config, yaml, json, properties | Config/Data | Validate syntax |
| cli, flyway, kubectl, terraform | CLI Tool | Run commands, parse output |

---

## Testing Pattern

For test frameworks (Cucumber, JUnit, Karate).

### run_signal.sh

```bash
#!/bin/bash
# run_signal.sh - Test execution signal
#
# Usage: run_signal.sh [--environment <env>] [--tags <tags>]

set -euo pipefail

ENVIRONMENT="${1:-local}"
TAGS="${2:-}"

echo "═══════════════════════════════════════════════════════════════"
echo "TEST SIGNAL"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Tags: ${TAGS:-all}"
echo ""

# TODO: Replace with actual test command
# Examples:
#   mvn test -Dcucumber.filter.tags="$TAGS"
#   ./gradlew test
#   customCli run test --environment "$ENVIRONMENT"
echo "Running tests..."
TEST_OUTPUT=$(mvn test 2>&1) || TEST_EXIT=$?
TEST_EXIT=${TEST_EXIT:-0}

# Parse results
# TODO: Adjust parsing based on test framework
TESTS_RUN=$(echo "$TEST_OUTPUT" | grep -oP 'Tests run: \K\d+' | tail -1 || echo "0")
FAILURES=$(echo "$TEST_OUTPUT" | grep -oP 'Failures: \K\d+' | tail -1 || echo "0")
ERRORS=$(echo "$TEST_OUTPUT" | grep -oP 'Errors: \K\d+' | tail -1 || echo "0")

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "RESULTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "{"
echo "  \"tests_run\": $TESTS_RUN,"
echo "  \"failures\": $FAILURES,"
echo "  \"errors\": $ERRORS,"
echo "  \"status\": \"$([ $TEST_EXIT -eq 0 ] && echo PASS || echo FAIL)\""
echo "}"

exit $TEST_EXIT
```

---

## API/Service Pattern

For REST APIs, GraphQL, HTTP services.

### run_signal.sh

```bash
#!/bin/bash
# run_signal.sh - API endpoint signal check
#
# Usage: run_signal.sh <base_url> <endpoint> [--method <GET|POST|PUT|DELETE>] [--data <json>]

set -euo pipefail

if [[ $# -lt 2 ]]; then
    echo "Usage: run_signal.sh <base_url> <endpoint> [options]"
    exit 1
fi

BASE_URL="$1"
ENDPOINT="$2"
METHOD="${3:-GET}"
DATA="${4:-}"

echo "═══════════════════════════════════════════════════════════════"
echo "API SIGNAL CHECK"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "URL: ${BASE_URL}${ENDPOINT}"
echo "Method: $METHOD"
echo ""

# Build curl command
CURL_CMD=(curl -s -w "\n%{http_code}\n%{time_total}" -X "$METHOD")
CURL_CMD+=(-H "Accept: application/json")
CURL_CMD+=(-H "Content-Type: application/json")

if [[ -n "$DATA" ]]; then
    CURL_CMD+=(-d "$DATA")
fi

CURL_CMD+=("${BASE_URL}${ENDPOINT}")

# Execute request
RESPONSE=$("${CURL_CMD[@]}" 2>&1) || true

# Parse response
BODY=$(echo "$RESPONSE" | head -n -2)
HTTP_CODE=$(echo "$RESPONSE" | tail -2 | head -1)
TIME_TOTAL=$(echo "$RESPONSE" | tail -1)

# Determine status
if [[ "$HTTP_CODE" =~ ^2 ]]; then
    STATUS="SUCCESS"
    EXIT_CODE=0
elif [[ "$HTTP_CODE" =~ ^4 ]]; then
    STATUS="CLIENT_ERROR"
    EXIT_CODE=4
else
    STATUS="SERVER_ERROR"
    EXIT_CODE=1
fi

echo "═══════════════════════════════════════════════════════════════"
echo "RESULTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "{"
echo "  \"http_status\": $HTTP_CODE,"
echo "  \"response_time_seconds\": $TIME_TOTAL,"
echo "  \"status\": \"$STATUS\""
echo "}"
echo ""
echo "Response Body:"
echo "$BODY" | head -c 500

exit $EXIT_CODE
```

---

## Build Pattern

For build tools (Maven, Gradle, npm).

### run_signal.sh

```bash
#!/bin/bash
# run_signal.sh - Build verification signal
#
# Usage: run_signal.sh [--skip-tests]

set -euo pipefail

SKIP_TESTS="${1:-}"

echo "═══════════════════════════════════════════════════════════════"
echo "BUILD SIGNAL"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# TODO: Replace with actual build command
# Examples:
#   mvn clean package -DskipTests
#   ./gradlew build
#   npm run build
BUILD_CMD="mvn clean package"
if [[ "$SKIP_TESTS" == "--skip-tests" ]]; then
    BUILD_CMD="$BUILD_CMD -DskipTests"
fi

echo "Running: $BUILD_CMD"
echo ""

BUILD_OUTPUT=$($BUILD_CMD 2>&1) || BUILD_EXIT=$?
BUILD_EXIT=${BUILD_EXIT:-0}

# Check for artifacts
# TODO: Adjust artifact path
ARTIFACT_PATH="target/*.jar"
ARTIFACT_COUNT=$(ls $ARTIFACT_PATH 2>/dev/null | wc -l || echo "0")

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "RESULTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "{"
echo "  \"build_status\": \"$([ $BUILD_EXIT -eq 0 ] && echo SUCCESS || echo FAILED)\","
echo "  \"artifacts_found\": $ARTIFACT_COUNT"
echo "}"

exit $BUILD_EXIT
```

---

## CLI Tool Pattern

For command-line tools (flyway, kubectl, terraform).

### run_signal.sh

```bash
#!/bin/bash
# run_signal.sh - CLI tool signal check
#
# Usage: run_signal.sh <command> [args...]

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: run_signal.sh <command> [args...]"
    exit 1
fi

COMMAND="$1"
shift
ARGS="$*"

echo "═══════════════════════════════════════════════════════════════"
echo "CLI SIGNAL"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Command: $COMMAND $ARGS"
echo ""

# Execute command
# TODO: Replace with actual CLI invocation
OUTPUT=$($COMMAND $ARGS 2>&1) || EXIT_CODE=$?
EXIT_CODE=${EXIT_CODE:-0}

echo "Output:"
echo "$OUTPUT"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "RESULTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "{"
echo "  \"command\": \"$COMMAND $ARGS\","
echo "  \"exit_code\": $EXIT_CODE,"
echo "  \"status\": \"$([ $EXIT_CODE -eq 0 ] && echo SUCCESS || echo FAILED)\""
echo "}"

exit $EXIT_CODE
```

---

## Config Validation Pattern

For configuration files (YAML, JSON, properties).

### run_signal.sh

```bash
#!/bin/bash
# run_signal.sh - Config validation signal
#
# Usage: run_signal.sh <config-file>

set -euo pipefail

if [[ $# -lt 1 ]]; then
    echo "Usage: run_signal.sh <config-file>"
    exit 1
fi

CONFIG_FILE="$1"

echo "═══════════════════════════════════════════════════════════════"
echo "CONFIG VALIDATION SIGNAL"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "File: $CONFIG_FILE"
echo ""

# Check file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "ERROR: File not found"
    exit 1
fi

# Validate based on extension
EXT="${CONFIG_FILE##*.}"
VALID=true
ERROR_MSG=""

case "$EXT" in
    yaml|yml)
        # TODO: Use yq or python for validation
        if command -v python3 &> /dev/null; then
            python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))" 2>&1 || {
                VALID=false
                ERROR_MSG="Invalid YAML syntax"
            }
        fi
        ;;
    json)
        if command -v jq &> /dev/null; then
            jq . "$CONFIG_FILE" > /dev/null 2>&1 || {
                VALID=false
                ERROR_MSG="Invalid JSON syntax"
            }
        elif command -v python3 &> /dev/null; then
            python3 -c "import json; json.load(open('$CONFIG_FILE'))" 2>&1 || {
                VALID=false
                ERROR_MSG="Invalid JSON syntax"
            }
        fi
        ;;
    *)
        echo "Warning: Unknown extension, skipping syntax check"
        ;;
esac

echo "═══════════════════════════════════════════════════════════════"
echo "RESULTS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "{"
echo "  \"file\": \"$CONFIG_FILE\","
echo "  \"valid\": $VALID,"
echo "  \"error\": \"$ERROR_MSG\""
echo "}"

$VALID && exit 0 || exit 1
```

---

## Output Format

All signal scripts should output structured JSON for AI parsing:

```json
{
  "status": "SUCCESS|FAILED|ERROR",
  "details": "Human-readable summary",
  "metrics": {
    "key": "value"
  }
}
```

Exit codes:
- `0` = Success
- `1` = Failure (generic)
- `4` = Client error (for API patterns)

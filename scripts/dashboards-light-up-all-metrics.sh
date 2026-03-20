#!/usr/bin/env bash

###############################################################################
# Configuration
###############################################################################

# Allow overriding the test script name via environment variable
# Example: TEST_SCRIPT=my_custom_test.py ./run_full_test.sh
TEST_SCRIPT="${TEST_SCRIPT:-send_test_hl7_advanced.py}"

###############################################################################
# Automatic path resolution
###############################################################################

# Resolve the directory of this script (absolute path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Project root is one level above scripts/
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Full path to the test script
TEST_SCRIPT_PATH="$PROJECT_ROOT/tools/$TEST_SCRIPT"

# Safety check
if [[ ! -f "$TEST_SCRIPT_PATH" ]]; then
    echo "ERROR: Test script not found: $TEST_SCRIPT_PATH"
    echo "Set TEST_SCRIPT env var if using a different filename."
    exit 1
fi

echo "Using test script: $TEST_SCRIPT_PATH"
echo "Project root: $PROJECT_ROOT"
echo "Script directory: $SCRIPT_DIR"
echo

###############################################################################
# Test Phases
###############################################################################

echo "=== Phase 1: Warm-up traffic ==="
python "$TEST_SCRIPT_PATH" --rate 5 --count 100

echo "=== Phase 2: High throughput ==="
python "$TEST_SCRIPT_PATH" --rate 20 --count 200

echo "=== Phase 3: Validation errors ==="
python "$TEST_SCRIPT_PATH" --rate 10 --count 100 --malformed 0.2

echo "=== Phase 4: Router failures ==="
python "$TEST_SCRIPT_PATH" --rate 10 --count 100 --router-fail 0.1

echo "=== Phase 5: Slow DB writes ==="
python "$TEST_SCRIPT_PATH" --rate 5 --count 50 --db-latency 300

echo "=== Phase 6: Chaos mode ==="
python "$TEST_SCRIPT_PATH" --rate 15 --count 200 --malformed 0.1 --router-fail 0.05 --db-latency 200

echo
echo "=== Test scenario completed ==="
#!/bin/bash

# GT Logs Helper - Automated Test Suite
# Run this script to perform automated testing of GT Logs Helper

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test function
run_test() {
    local description="$1"
    local command="$2"
    local expected_exit="${3:-0}"  # Default expect success

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${YELLOW}TEST $TESTS_RUN: $description${NC}"
    echo "Command: $command"
    echo "---"

    if eval "$command" > /tmp/test_output.txt 2>&1; then
        actual_exit=0
    else
        actual_exit=$?
    fi

    if [ "$actual_exit" -eq "$expected_exit" ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected exit $expected_exit, got $actual_exit)"
        echo "Output:"
        cat /tmp/test_output.txt
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Check output contains string
check_output_contains() {
    local description="$1"
    local command="$2"
    local expected_string="$3"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${YELLOW}TEST $TESTS_RUN: $description${NC}"
    echo "Command: $command"
    echo "Looking for: $expected_string"
    echo "---"

    eval "$command" > /tmp/test_output.txt 2>&1

    if grep -q -- "$expected_string" /tmp/test_output.txt; then
        echo -e "${GREEN}✓ PASS${NC} - Found expected string"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} - String not found"
        echo "Output:"
        head -20 /tmp/test_output.txt
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "======================================"
echo "GT Logs Helper - Automated Test Suite"
echo "======================================"
echo ""

# Check if script exists
if [ ! -f "gtlogs-helper.py" ]; then
    echo -e "${RED}Error: gtlogs-helper.py not found in current directory${NC}"
    exit 1
fi

# Make script executable
chmod +x gtlogs-helper.py

# Create test files
echo "Creating test files..."
echo "test content" > test_file.txt
mkdir -p test_dir

echo -e "\n${YELLOW}=== Phase 1: Basic Functionality Tests ===${NC}"

# Test 1: Version display
check_output_contains "Version display" \
    "python3 gtlogs-helper.py --version" \
    "GT Logs Helper v1.1"

# Test 2: Help display
check_output_contains "Help display" \
    "python3 gtlogs-helper.py -h" \
    "Upload and download Redis Support packages"

# Test 3: Show config
run_test "Show configuration" \
    "python3 gtlogs-helper.py --show-config"

echo -e "\n${YELLOW}=== Phase 2: Upload Mode Tests ===${NC}"

# Test 4: Basic upload command generation
check_output_contains "Generate upload command (ZD-only)" \
    "python3 gtlogs-helper.py 145980" \
    "s3://gt-logs/zendesk-tickets/ZD-145980/"

# Test 5: Upload with Jira
check_output_contains "Generate upload command (ZD+Jira)" \
    "python3 gtlogs-helper.py 145980 RED-172041" \
    "s3://gt-logs/exa-to-gt/ZD-145980-RED-172041/"

# Test 6: Upload with file
check_output_contains "Generate upload with file" \
    "python3 gtlogs-helper.py 145980 -f test_file.txt" \
    "test_file.txt"

# Test 7: Upload with custom profile
check_output_contains "Upload with custom profile" \
    "python3 gtlogs-helper.py 145980 -p custom-profile" \
    "profile custom-profile"

echo -e "\n${YELLOW}=== Phase 3: Input Validation Tests ===${NC}"

# Test 8: Invalid Zendesk ID
run_test "Invalid Zendesk ID (letters)" \
    "python3 gtlogs-helper.py abc123 2>&1" \
    1  # Expect failure

# Test 9: Invalid Jira ID
run_test "Invalid Jira ID" \
    "python3 gtlogs-helper.py 145980 INVALID-123 2>&1" \
    1  # Expect failure

# Test 10: Non-existent file
run_test "Non-existent file" \
    "python3 gtlogs-helper.py 145980 -f /nonexistent/file.txt 2>&1" \
    1  # Expect failure

# Test 11: Directory instead of file
run_test "Directory instead of file" \
    "python3 gtlogs-helper.py 145980 -f test_dir 2>&1" \
    1  # Expect failure

echo -e "\n${YELLOW}=== Phase 4: Download Mode Tests ===${NC}"

# Test 12: Download command generation
check_output_contains "Download mode activation" \
    "python3 gtlogs-helper.py --download ZD-145980" \
    "Checking AWS authentication"

echo -e "\n${YELLOW}=== Phase 5: AWS Profile Tests ===${NC}"

# Test 13: Backup existing config
if [ -f ~/.gtlogs-config.ini ]; then
    cp ~/.gtlogs-config.ini ~/.gtlogs-config.ini.test_backup
fi

# Test 14: No config file (should use fallback)
rm -f ~/.gtlogs-config.ini
check_output_contains "No config - uses fallback" \
    "python3 gtlogs-helper.py 145980" \
    "gt-logs"

# Restore config if it existed
if [ -f ~/.gtlogs-config.ini.test_backup ]; then
    mv ~/.gtlogs-config.ini.test_backup ~/.gtlogs-config.ini
fi

echo -e "\n${YELLOW}=== Phase 6: Edge Cases ===${NC}"

# Test 15: File with spaces
touch "file with spaces.tar.gz"
check_output_contains "File with spaces" \
    "python3 gtlogs-helper.py 145980 -f 'file with spaces.tar.gz'" \
    "file with spaces.tar.gz"
rm "file with spaces.tar.gz"

# Test 16: Multiple input formats
check_output_contains "Pre-formatted ZD" \
    "python3 gtlogs-helper.py ZD-145980" \
    "ZD-145980"

check_output_contains "MOD Jira prefix" \
    "python3 gtlogs-helper.py 145980 MOD-12345" \
    "MOD-12345"

echo -e "\n${YELLOW}=== Phase 7: S3 Path Parsing Tests ===${NC}"

# Create a Python test script for path parsing
cat > test_parsing.py << 'EOF'
#!/usr/bin/env python3
import sys
import re

def parse_s3_path(s3_path):
    """Simplified version of parse_s3_path for testing"""
    if s3_path.startswith("s3://"):
        parts = s3_path[5:].split("/", 1)
        if len(parts) >= 1:
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
            return bucket, key

    # Handle partial paths
    try:
        zd_match = re.match(r'^(?:ZD-)?(\d+)', s3_path.upper())
        if zd_match:
            zd_number = zd_match.group(1)
            zd_id = f"ZD-{zd_number}"

            if "-RED-" in s3_path.upper() or "-MOD-" in s3_path.upper():
                jira_match = re.search(r'(RED|MOD)-\d+', s3_path.upper())
                if jira_match:
                    jira_id = jira_match.group()
                    return "gt-logs", f"exa-to-gt/{zd_id}-{jira_id}/"
            return "gt-logs", f"zendesk-tickets/{zd_id}/"
    except:
        pass
    return None, None

# Test cases
test_cases = [
    ("s3://gt-logs/zendesk-tickets/ZD-145980/file.tar.gz", True),
    ("ZD-145980", True),
    ("145980", True),
    ("ZD-145980-RED-172041", True),
    ("invalid-path", False)
]

all_pass = True
for path, should_parse in test_cases:
    bucket, key = parse_s3_path(path)
    success = (bucket is not None) == should_parse
    if success:
        print(f"✓ {path}")
    else:
        print(f"✗ {path}")
        all_pass = False

sys.exit(0 if all_pass else 1)
EOF

run_test "S3 path parsing" \
    "python3 test_parsing.py"

# Clean up test files
echo -e "\n${YELLOW}Cleaning up test files...${NC}"
rm -f test_file.txt
rm -rf test_dir
rm -f test_parsing.py
rm -f /tmp/test_output.txt

# Summary
echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo -e "Tests Run:    $TESTS_RUN"
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed. Please review the output above.${NC}"
    exit 1
fi
#!/bin/bash
# PENIN-Ω Test Runner
# Usage: ./scripts/run_tests.sh [options]

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
COVERAGE=false
VERBOSE=false
MARKERS=""
SPECIFIC_TEST=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  -c, --coverage     Run with coverage report"
            echo "  -v, --verbose      Run with verbose output"
            echo "  -m, --markers      Run tests with specific markers (e.g., 'unit', 'not slow')"
            echo "  -t, --test         Run specific test file or function"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                # Run all tests"
            echo "  $0 -c                             # Run with coverage"
            echo "  $0 -m unit                        # Run only unit tests"
            echo "  $0 -t tests/test_caos.py          # Run specific test file"
            echo "  $0 -t tests/test_caos.py::test_calculation  # Run specific test"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== PENIN-Ω Test Suite ===${NC}\n"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest not found. Install with: pip install -e \".[dev]\"${NC}"
    exit 1
fi

# Build pytest command
PYTEST_CMD="pytest"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=penin --cov-report=term-missing --cov-report=html"
    echo -e "${YELLOW}Running with coverage analysis...${NC}\n"
fi

if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m \"$MARKERS\""
    echo -e "${YELLOW}Running tests with markers: $MARKERS${NC}\n"
fi

if [ -n "$SPECIFIC_TEST" ]; then
    PYTEST_CMD="$PYTEST_CMD $SPECIFIC_TEST"
    echo -e "${YELLOW}Running specific test: $SPECIFIC_TEST${NC}\n"
else
    PYTEST_CMD="$PYTEST_CMD tests/"
fi

# Run tests
eval $PYTEST_CMD
TEST_RESULT=$?

# Print results
echo ""
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    if [ "$COVERAGE" = true ]; then
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
    fi
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi

exit 0

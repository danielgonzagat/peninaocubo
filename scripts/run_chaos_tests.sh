#!/bin/bash
#
# Chaos Engineering Test Runner
# ==============================
#
# Helper script to run chaos engineering tests with various configurations.
#
# Usage:
#   ./scripts/run_chaos_tests.sh [options]
#
# Options:
#   --quick       Run only quick chaos tests
#   --full        Run all chaos tests including slow ones
#   --docker      Run tests in Docker environment with Toxiproxy
#   --local       Run tests locally (default)
#   --verbose     Show detailed output
#   --coverage    Generate coverage report
#   --help        Show this help message

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
MODE="local"
VERBOSITY="-v"
COVERAGE=""
TEST_FILTER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)
            TEST_FILTER="-m 'chaos and not slow'"
            shift
            ;;
        --full)
            TEST_FILTER="-m chaos"
            shift
            ;;
        --docker)
            MODE="docker"
            shift
            ;;
        --local)
            MODE="local"
            shift
            ;;
        --verbose)
            VERBOSITY="-vv -s"
            shift
            ;;
        --coverage)
            COVERAGE="--cov=penin --cov-report=html --cov-report=term"
            shift
            ;;
        --help)
            head -n 20 "$0" | tail -n +3 | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# Set default test filter if none specified
if [ -z "$TEST_FILTER" ]; then
    TEST_FILTER="-m chaos"
fi

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    PENIN-Ω Chaos Engineering Test Suite Runner          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Local mode
if [ "$MODE" = "local" ]; then
    echo -e "${YELLOW}→ Running tests locally...${NC}"
    echo ""
    
    # Check if pytest is installed
    if ! command -v pytest &> /dev/null; then
        echo -e "${RED}✗ pytest not found. Installing...${NC}"
        pip install pytest pytest-asyncio pytest-timeout
    fi
    
    # Check if dependencies are installed
    if ! python -c "import penin" 2>/dev/null; then
        echo -e "${YELLOW}→ Installing penin package...${NC}"
        pip install -e .
    fi
    
    # Run tests
    echo -e "${GREEN}→ Running chaos tests...${NC}"
    echo ""
    
    pytest tests/test_chaos_engineering.py $TEST_FILTER $VERBOSITY $COVERAGE
    
    TEST_EXIT_CODE=$?
    
    echo ""
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ All chaos tests passed!${NC}"
    else
        echo -e "${RED}❌ Some chaos tests failed!${NC}"
        exit $TEST_EXIT_CODE
    fi
    
    # Show coverage report location if generated
    if [ -n "$COVERAGE" ]; then
        echo ""
        echo -e "${BLUE}→ Coverage report generated at: htmlcov/index.html${NC}"
    fi
fi

# Docker mode
if [ "$MODE" = "docker" ]; then
    echo -e "${YELLOW}→ Running tests in Docker environment with Toxiproxy...${NC}"
    echo ""
    
    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ docker-compose not found. Please install Docker Compose.${NC}"
        exit 1
    fi
    
    # Navigate to deploy directory
    cd "$(dirname "$0")/../deploy"
    
    # Start services
    echo -e "${GREEN}→ Starting chaos testing environment...${NC}"
    docker-compose -f docker-compose.chaos.yml up -d toxiproxy sigma-guard-test sr-omega-test
    
    # Wait for services to be ready
    echo -e "${YELLOW}→ Waiting for services to be ready...${NC}"
    sleep 10
    
    # Check service health
    echo -e "${BLUE}→ Checking service health...${NC}"
    
    if docker-compose -f docker-compose.chaos.yml exec -T toxiproxy curl -sf http://localhost:8474/version &> /dev/null; then
        echo -e "${GREEN}  ✓ Toxiproxy is healthy${NC}"
    else
        echo -e "${YELLOW}  ⚠ Toxiproxy might not be ready yet${NC}"
    fi
    
    # Run tests in container
    echo ""
    echo -e "${GREEN}→ Running chaos tests in container...${NC}"
    echo ""
    
    docker-compose -f docker-compose.chaos.yml run --rm chaos-tests \
        pytest tests/test_chaos_engineering.py $TEST_FILTER $VERBOSITY
    
    TEST_EXIT_CODE=$?
    
    # Cleanup
    echo ""
    echo -e "${YELLOW}→ Cleaning up containers...${NC}"
    docker-compose -f docker-compose.chaos.yml down -v
    
    echo ""
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ All chaos tests passed!${NC}"
    else
        echo -e "${RED}❌ Some chaos tests failed!${NC}"
        exit $TEST_EXIT_CODE
    fi
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Chaos testing complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

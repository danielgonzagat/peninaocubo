#!/bin/bash
# PENIN-Ω Health Check Script
# Validates all critical components and infrastructure

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
ERRORS=0

echo "🔍 PENIN-Ω Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Helper functions
check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((SUCCESS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

# 1. Python Environment
echo "📦 Python Environment"
echo "─────────────────────"

if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version | awk '{print $2}')
    if [[ "$PY_VERSION" =~ ^3\.(11|12) ]]; then
        check_pass "Python version: $PY_VERSION"
    else
        check_warn "Python version: $PY_VERSION (expected 3.11 or 3.12)"
    fi
else
    check_fail "Python 3 not found"
fi

# 2. Package Installation
echo ""
echo "📚 Package Status"
echo "─────────────────"

cd "$PROJECT_ROOT"

if python3 -c "import penin" 2>/dev/null; then
    check_pass "penin package importable"
    VERSION=$(python3 -c "import penin; print(penin.__version__)" 2>/dev/null || echo "unknown")
    echo "   Version: $VERSION"
else
    check_fail "penin package not installed (run: pip install -e .)"
fi

# 3. Critical Modules
echo ""
echo "🧩 Critical Modules"
echo "───────────────────"

MODULES=(
    "penin.engine.master_equation"
    "penin.engine.caos_plus"
    "penin.math.linf"
    "penin.guard.sigma_guard_complete"
    "penin.ethics.laws"
    "penin.ethics.agape"
)

for MODULE in "${MODULES[@]}"; do
    if python3 -c "import $MODULE" 2>/dev/null; then
        check_pass "$MODULE"
    else
        check_fail "$MODULE (import failed)"
    fi
done

# 4. Configuration Files
echo ""
echo "⚙️  Configuration Files"
echo "──────────────────────"

CONFIG_FILES=(
    "pyproject.toml"
    "mkdocs.yml"
    "CODE_OF_CONDUCT.md"
    "GOVERNANCE.md"
    ".github/workflows/ci-enhanced.yml"
    "deploy/docker-compose.yml"
    "deploy/docker-compose.observability.yml"
)

for FILE in "${CONFIG_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$FILE" ]; then
        check_pass "$FILE"
    else
        check_fail "$FILE (missing)"
    fi
done

# 5. Observability Stack
echo ""
echo "📊 Observability Stack"
echo "──────────────────────"

OBS_FILES=(
    "deploy/prometheus/prometheus-enhanced.yml"
    "deploy/prometheus/alerts/penin-alerts.yml"
    "deploy/loki/config.yml"
    "deploy/tempo/config.yml"
    "deploy/alertmanager/config.yml"
    "deploy/grafana/datasources-full.yml"
    "deploy/grafana/dashboards/penin-omega-overview.json"
)

for FILE in "${OBS_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$FILE" ]; then
        check_pass "$FILE"
    else
        check_fail "$FILE (missing)"
    fi
done

# 6. Tests
echo ""
echo "🧪 Test Suite"
echo "─────────────"

if [ -d "$PROJECT_ROOT/tests" ]; then
    TEST_COUNT=$(find "$PROJECT_ROOT/tests" -name "test_*.py" | wc -l)
    check_pass "Test files found: $TEST_COUNT"
    
    if command -v pytest &> /dev/null; then
        check_pass "pytest available"
        # Run quick smoke test
        if pytest "$PROJECT_ROOT/tests" --co -q &> /dev/null; then
            check_pass "Tests collectable"
        else
            check_warn "Some tests not collectable"
        fi
    else
        check_warn "pytest not installed"
    fi
else
    check_fail "tests/ directory missing"
fi

# 7. Documentation
echo ""
echo "📖 Documentation"
echo "────────────────"

DOC_FILES=(
    "README.md"
    "CHANGELOG.md"
    "CONTRIBUTING.md"
    "docs/index.md"
    "docs/architecture.md"
    "docs/ethics.md"
)

for FILE in "${DOC_FILES[@]}"; do
    if [ -f "$PROJECT_ROOT/$FILE" ]; then
        check_pass "$FILE"
    else
        check_warn "$FILE (missing)"
    fi
done

# 8. Docker
echo ""
echo "🐳 Docker"
echo "─────────"

if command -v docker &> /dev/null; then
    check_pass "Docker available"
    
    if [ -f "$PROJECT_ROOT/deploy/Dockerfile" ]; then
        check_pass "Dockerfile present"
    else
        check_fail "Dockerfile missing"
    fi
    
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1; then
        check_pass "Docker Compose available"
    else
        check_warn "Docker Compose not available"
    fi
else
    check_warn "Docker not installed"
fi

# 9. Code Quality Tools
echo ""
echo "🔧 Code Quality Tools"
echo "─────────────────────"

TOOLS=(
    "ruff:Ruff linter"
    "black:Black formatter"
    "mypy:Mypy type checker"
    "pytest:Pytest framework"
)

for TOOL_INFO in "${TOOLS[@]}"; do
    IFS=':' read -r TOOL DESC <<< "$TOOL_INFO"
    if command -v "$TOOL" &> /dev/null; then
        check_pass "$DESC"
    else
        check_warn "$DESC (not installed)"
    fi
done

# 10. Git
echo ""
echo "🌿 Git Repository"
echo "─────────────────"

if [ -d "$PROJECT_ROOT/.git" ]; then
    check_pass "Git repository initialized"
    
    if git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD &> /dev/null; then
        BRANCH=$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD)
        echo "   Branch: $BRANCH"
        check_pass "Git HEAD valid"
    fi
    
    # Check for uncommitted changes
    if ! git -C "$PROJECT_ROOT" diff-index --quiet HEAD -- 2>/dev/null; then
        check_warn "Uncommitted changes present"
    else
        check_pass "Working directory clean"
    fi
else
    check_fail "Not a Git repository"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✓ Passed:  $SUCCESS${NC}"
echo -e "${YELLOW}⚠ Warnings: $WARNINGS${NC}"
echo -e "${RED}✗ Errors:   $ERRORS${NC}"
echo ""

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}❌ Health check FAILED${NC}"
    echo "Please fix errors before proceeding."
    exit 1
elif [ $WARNINGS -gt 5 ]; then
    echo -e "${YELLOW}⚠️  Health check PASSED with warnings${NC}"
    echo "Consider addressing warnings for best experience."
    exit 0
else
    echo -e "${GREEN}✅ Health check PASSED${NC}"
    echo "System is healthy and ready!"
    exit 0
fi

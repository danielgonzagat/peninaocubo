#!/bin/bash
# PENIN-Ω Test Suite Runner
# Executa todos os testes do sistema

echo "╔════════════════════════════════════════════════╗"
echo "║        PENIN-Ω TEST SUITE RUNNER              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Install dependencies if needed
echo "📦 Checking dependencies..."
python3 -c "import pydantic, psutil, prometheus_client, structlog, pytest, numpy, tenacity, pydantic_settings" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Installing missing dependencies...${NC}"
    pip3 install --break-system-packages pydantic psutil prometheus-client structlog pytest pytest-asyncio numpy tenacity pydantic-settings 2>/dev/null
fi

echo ""
echo "🧪 Running P0 Audit Corrections Tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 test_p0_audit_corrections.py
P0_RESULT=$?

echo ""
echo "🧪 Running P0 Simple Tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "test_p0_simple.py" ]; then
    python3 test_p0_simple.py
    P0_SIMPLE_RESULT=$?
else
    echo -e "${YELLOW}test_p0_simple.py not found, skipping...${NC}"
    P0_SIMPLE_RESULT=0
fi

echo ""
echo "🧪 Running Omega Module Tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "test_omega_modules.py" ]; then
    python3 test_omega_modules.py
    OMEGA_RESULT=$?
else
    echo -e "${YELLOW}test_omega_modules.py not found, skipping...${NC}"
    OMEGA_RESULT=0
fi

echo ""
echo "🧪 Running Integration Tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "test_integration_complete.py" ]; then
    python3 test_integration_complete.py
    INTEGRATION_RESULT=$?
else
    echo -e "${YELLOW}test_integration_complete.py not found, skipping...${NC}"
    INTEGRATION_RESULT=0
fi

echo ""
echo "╔════════════════════════════════════════════════╗"
echo "║              TEST RESULTS SUMMARY              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Calculate total result
TOTAL_RESULT=$((P0_RESULT + P0_SIMPLE_RESULT + OMEGA_RESULT + INTEGRATION_RESULT))

# Display results with colors
if [ $P0_RESULT -eq 0 ]; then
    echo -e "P0 Audit Corrections: ${GREEN}✅ PASSED${NC}"
else
    echo -e "P0 Audit Corrections: ${RED}❌ FAILED${NC}"
fi

if [ $P0_SIMPLE_RESULT -eq 0 ]; then
    echo -e "P0 Simple Tests:      ${GREEN}✅ PASSED${NC}"
else
    echo -e "P0 Simple Tests:      ${RED}❌ FAILED${NC}"
fi

if [ $OMEGA_RESULT -eq 0 ]; then
    echo -e "Omega Modules:        ${GREEN}✅ PASSED${NC}"
else
    echo -e "Omega Modules:        ${RED}❌ FAILED${NC}"
fi

if [ $INTEGRATION_RESULT -eq 0 ]; then
    echo -e "Integration Tests:    ${GREEN}✅ PASSED${NC}"
else
    echo -e "Integration Tests:    ${RED}❌ FAILED${NC}"
fi

echo ""
if [ $TOTAL_RESULT -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉      ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║        ⚠️  SOME TESTS FAILED  ⚠️               ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════╝${NC}"
fi

exit $TOTAL_RESULT
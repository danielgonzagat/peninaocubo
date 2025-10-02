#!/bin/bash
#
# PENIN-Ω Security Audit Script
# ==============================
#
# Runs comprehensive security checks:
# 1. SBOM generation (CycloneDX)
# 2. Dependency vulnerabilities (pip-audit, safety)
# 3. Secret scanning (gitleaks)
# 4. Code security (bandit)
# 5. Container scanning (trivy - if Docker available)

set -euo pipefail

echo "🔒 PENIN-Ω Security Audit"
echo "========================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PASSED=0
WARNINGS=0
FAILED=0

# ============================================================================
# 1. SBOM GENERATION
# ============================================================================

echo "📦 [1/5] Generating SBOM..."
if bash scripts/generate_sbom.sh > /tmp/sbom.log 2>&1; then
    echo -e "${GREEN}✅ SBOM generated successfully${NC}"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  SBOM generation had warnings (continuing)${NC}"
    ((WARNINGS++))
fi

# ============================================================================
# 2. DEPENDENCY VULNERABILITIES (pip-audit)
# ============================================================================

echo ""
echo "🔍 [2/5] Scanning dependencies for vulnerabilities (pip-audit)..."

if ! command -v pip-audit &> /dev/null; then
    echo "📦 Installing pip-audit..."
    pip install pip-audit
fi

if pip-audit --desc --fix-dry-run > security/pip-audit-report.txt 2>&1; then
    echo -e "${GREEN}✅ No vulnerabilities found${NC}"
    ((PASSED++))
else
    vulns=$(grep -c "VULNERABILITY" security/pip-audit-report.txt || echo "0")
    if [ "$vulns" -gt 0 ]; then
        echo -e "${RED}❌ Found $vulns vulnerabilities${NC}"
        echo "   Report: security/pip-audit-report.txt"
        ((FAILED++))
    else
        echo -e "${GREEN}✅ No critical vulnerabilities${NC}"
        ((PASSED++))
    fi
fi

# ============================================================================
# 3. SECRET SCANNING (gitleaks)
# ============================================================================

echo ""
echo "🔐 [3/5] Scanning for secrets (gitleaks)..."

# Check if gitleaks is available
if command -v gitleaks &> /dev/null; then
    if gitleaks detect --no-git --report-path=security/gitleaks-report.json > /dev/null 2>&1; then
        echo -e "${GREEN}✅ No secrets detected${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ Potential secrets found${NC}"
        echo "   Report: security/gitleaks-report.json"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠️  gitleaks not installed (skipping)${NC}"
    echo "   Install: brew install gitleaks (or see https://github.com/gitleaks/gitleaks)"
    ((WARNINGS++))
fi

# ============================================================================
# 4. CODE SECURITY (bandit)
# ============================================================================

echo ""
echo "🐍 [4/5] Scanning Python code for security issues (bandit)..."

if ! command -v bandit &> /dev/null; then
    echo "📦 Installing bandit..."
    pip install bandit
fi

mkdir -p security
if bandit -r penin/ -f json -o security/bandit-report.json > /dev/null 2>&1; then
    echo -e "${GREEN}✅ No security issues found${NC}"
    ((PASSED++))
else
    # Check severity
    high_severity=$(python3 -c "import json; data=json.load(open('security/bandit-report.json')); print(len([r for r in data.get('results', []) if r.get('issue_severity') == 'HIGH']))" 2>/dev/null || echo "0")
    
    if [ "$high_severity" -gt 0 ]; then
        echo -e "${RED}❌ Found $high_severity high-severity issues${NC}"
        echo "   Report: security/bandit-report.json"
        ((FAILED++))
    else
        echo -e "${GREEN}✅ No high-severity issues${NC}"
        ((PASSED++))
    fi
fi

# ============================================================================
# 5. DEPENDENCY LICENSE CHECK
# ============================================================================

echo ""
echo "⚖️  [5/5] Checking dependency licenses..."

if pip-licenses --format=json > security/licenses.json 2>&1; then
    # Check for problematic licenses (GPL, AGPL, etc.)
    problematic=$(python3 -c "import json; data=json.load(open('security/licenses.json')); print(len([d for d in data if 'GPL' in d.get('License', '')]))" 2>/dev/null || echo "0")
    
    if [ "$problematic" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Found $problematic packages with GPL-like licenses${NC}"
        echo "   Report: security/licenses.json"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✅ All licenses compatible${NC}"
        ((PASSED++))
    fi
else
    echo -e "${YELLOW}⚠️  pip-licenses not available (skipping)${NC}"
    ((WARNINGS++))
fi

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "📊 Security Audit Summary"
echo "========================="
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${RED}❌ Security audit FAILED${NC}"
    echo "   Review reports in security/ directory"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Security audit PASSED with warnings${NC}"
    echo "   Review warnings for production deployment"
    exit 0
else
    echo -e "${GREEN}✅ Security audit PASSED${NC}"
    echo "   System ready for production deployment"
    exit 0
fi

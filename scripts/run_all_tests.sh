#!/bin/bash
# PENIN-Ω Full Test Suite Runner
# Runs all tests and generates detailed report

set -e

echo "🧪 PENIN-Ω Full Test Suite"
echo "==========================="
echo ""

# Ensure dependencies are installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Run ./scripts/setup_dev_env.sh first"
    exit 1
fi

echo "📊 Running full test suite..."
echo "⏱️  This may take a few minutes..."
echo ""

# Run tests with detailed output
pytest tests/ -v --tb=short --maxfail=10 > test_results_full.log 2>&1 || true

# Extract summary
echo "📈 Test Summary:"
echo "================"
tail -50 test_results_full.log | grep -E "(passed|failed|error|PASSED|FAILED|ERROR)" | tail -20

echo ""
echo "💾 Full results saved to: test_results_full.log"
echo ""

# Count results
TOTAL=$(grep -oP "collected \K\d+" test_results_full.log | head -1 || echo "0")
PASSED=$(grep -oP "\d+ passed" test_results_full.log | grep -oP "\d+" || echo "0")
FAILED=$(grep -oP "\d+ failed" test_results_full.log | grep -oP "\d+" || echo "0")
ERRORS=$(grep -oP "\d+ error" test_results_full.log | grep -oP "\d+" || echo "0")

echo "📊 Quick Stats:"
echo "  Total collected: $TOTAL"
echo "  Passed: $PASSED"
echo "  Failed: $FAILED"
echo "  Errors: $ERRORS"
echo ""

if [ "$PASSED" -gt 0 ] && [ "$FAILED" -eq 0 ] && [ "$ERRORS" -eq 0 ]; then
    echo "✅ All tests passed!"
elif [ "$PASSED" -gt 0 ]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
    echo "⚠️  Some tests failed or errored (${PASS_RATE}% pass rate)"
    echo "   Review test_results_full.log for details"
else
    echo "❌ Critical issues detected"
    echo "   Review test_results_full.log for details"
fi
echo ""

# Suggest next steps
if [ "$ERRORS" -gt 0 ]; then
    echo "🔧 Next steps:"
    echo "  1. Check test_results_full.log for import errors"
    echo "  2. Install missing dependencies"
    echo "  3. Re-run this script"
fi
echo ""

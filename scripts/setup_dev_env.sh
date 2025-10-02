#!/bin/bash
# PENIN-Ω Development Environment Setup
# Installs all dependencies for development and testing

set -e

echo "🔧 PENIN-Ω Development Environment Setup"
echo "=========================================="
echo ""

# Check Python version
echo "📍 Checking Python version..."
python3 --version
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
python3 -m pip install --upgrade pip --quiet
echo "✅ pip upgraded"
echo ""

# Install core package in editable mode
echo "📦 Installing PENIN-Ω core package..."
pip install -e . --quiet
echo "✅ Core package installed"
echo ""

# Install dev dependencies
echo "🛠️  Installing development dependencies..."
pip install -e ".[dev]" --quiet
echo "✅ Dev dependencies installed"
echo ""

# Install full dependencies (optional integrations)
echo "🌟 Installing full dependencies (SOTA integrations)..."
pip install -e ".[full]" --quiet 2>&1 | grep -v "WARNING" || true
echo "✅ Full dependencies installed"
echo ""

# Verify critical packages
echo "📋 Installed critical packages:"
pip list | grep -E "(pytest|ruff|black|mypy|hypothesis|numpy|pydantic|rich)" || echo "  (some packages may be missing)"
echo ""

# Test imports
echo "🧪 Testing critical imports..."
python3 -c "
import penin
from penin.core import caos
from penin.math import linf
from penin.engine import master_equation
print('  ✅ All critical imports successful')
print(f'  📌 PENIN-Ω version: {penin.__version__}')
"
echo ""

echo "✅ Development environment ready!"
echo ""
echo "Next steps:"
echo "  1. Run tests: ./scripts/run_all_tests.sh"
echo "  2. Run demo: python examples/demo_60s_complete.py"
echo "  3. Check linting: ruff check ."
echo ""

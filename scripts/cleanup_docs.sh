#!/bin/bash
# PENIN-Ω Documentation Cleanup
# Archives old status reports and consolidates documentation

set -e

echo "📁 PENIN-Ω Documentation Cleanup"
echo "================================="
echo ""

# Create archive directory
mkdir -p docs/archive/deprecated/sessions/2025-10-01/

# Count current files
BEFORE=$(find docs/ -name "*.md" | wc -l)
echo "📊 Current state: $BEFORE markdown files in docs/"
echo ""

# Archive old status reports
echo "🗂️  Archiving old status reports..."

# Move status reports from sessions
find docs/archive/sessions/2025-10-01/ -name "*STATUS*.md" -o -name "*RESUMO*.md" -o -name "*SESSAO*.md" 2>/dev/null | while read f; do
  if [ -f "$f" ]; then
    echo "  Moving: $f"
    mv "$f" docs/archive/deprecated/sessions/2025-10-01/ 2>/dev/null || true
  fi
done

# Move transformation reports
find docs/archive/ -maxdepth 1 -name "*TRANSFORMATION*.md" -o -name "*FINAL*.md" 2>/dev/null | while read f; do
  if [ -f "$f" ]; then
    echo "  Moving: $f"
    mv "$f" docs/archive/deprecated/ 2>/dev/null || true
  fi
done

echo "✅ Archiving complete"
echo ""

# Count after cleanup
AFTER=$(find docs/ -name "*.md" -not -path "*/archive/deprecated/*" | wc -l)
ARCHIVED=$((BEFORE - AFTER))

echo "📈 Cleanup results:"
echo "  Before: $BEFORE files"
echo "  After: $AFTER files"
echo "  Archived: $ARCHIVED files"
echo ""

# List essential docs
echo "📚 Essential documentation (should remain):"
find docs/ -maxdepth 1 -name "*.md" | sort
echo ""

echo "✅ Documentation cleanup complete!"
echo ""
echo "Next steps:"
echo "  1. Review docs/INDEX.md"
echo "  2. Ensure all links in README.md work"
echo "  3. Create docs/operations/README.md if missing"
echo ""

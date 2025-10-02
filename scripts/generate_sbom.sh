#!/bin/bash
#
# Generate Software Bill of Materials (SBOM)
# ===========================================
#
# Creates CycloneDX SBOM for PENIN-Ω dependencies.
# Required for security audit and supply chain transparency.

set -euo pipefail

echo "🔍 Generating SBOM for PENIN-Ω..."

# Check if cyclonedx-bom is installed
if ! command -v cyclonedx-py &> /dev/null; then
    echo "📦 Installing cyclonedx-bom..."
    pip install cyclonedx-bom
fi

# Generate SBOM from requirements
echo "📝 Generating SBOM from requirements.txt..."
cyclonedx-py requirements \
    -i requirements.txt \
    -o sbom.json \
    --format json

echo "✅ SBOM generated: sbom.json"

# Also generate XML format (some tools prefer this)
cyclonedx-py requirements \
    -i requirements.txt \
    -o sbom.xml \
    --format xml

echo "✅ SBOM generated: sbom.xml"

# Generate from pyproject.toml (more complete)
if [ -f "pyproject.toml" ]; then
    echo "📝 Generating SBOM from pyproject.toml..."
    cyclonedx-py poetry \
        -o sbom_full.json \
        --format json 2>/dev/null || true
fi

# Print summary
echo ""
echo "📊 SBOM Summary:"
if [ -f "sbom.json" ]; then
    # Count components
    components=$(python3 -c "import json; data=json.load(open('sbom.json')); print(len(data.get('components', [])))" 2>/dev/null || echo "N/A")
    echo "  - Total components: $components"
    echo "  - Format: CycloneDX JSON"
    echo "  - Location: sbom.json, sbom.xml"
fi

echo ""
echo "✅ SBOM generation complete!"
echo "   Use for: Supply chain security, vulnerability scanning, compliance"

#!/bin/bash
set -e

# PENIN-Ω Entrypoint Script
# Handles initialization, health checks, and graceful shutdown

echo "🚀 Starting PENIN-Ω (IA³ Auto-Evolution System)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Display environment info
echo "📊 Environment:"
echo "  • Python: $(python --version)"
echo "  • Platform: $(uname -m)"
echo "  • User: $(whoami)"
echo "  • Working Dir: $(pwd)"

# Validate required environment variables
REQUIRED_VARS=(
    "PENIN_DATA_DIR"
    "PENIN_LOG_DIR"
)

for VAR in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        echo "❌ ERROR: Required environment variable $VAR is not set"
        exit 1
    fi
done

# Create directories if they don't exist
mkdir -p "$PENIN_DATA_DIR" "$PENIN_LOG_DIR"

# Initialize WORM ledger if not exists
if [ ! -f "$PENIN_DATA_DIR/worm_ledger.jsonl" ]; then
    echo "🔒 Initializing WORM Ledger..."
    echo '{"type":"genesis","timestamp":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","version":"1.0","hash":"genesis"}' \
        > "$PENIN_DATA_DIR/worm_ledger.jsonl"
fi

# Validate configuration
echo "🔧 Validating configuration..."
if ! python -c "from penin.config import PeninConfig; PeninConfig()" 2>/dev/null; then
    echo "⚠️  WARNING: Configuration validation failed, using defaults"
fi

# Pre-flight checks
echo "✓ Data directory: $PENIN_DATA_DIR"
echo "✓ Log directory: $PENIN_LOG_DIR"
echo "✓ Metrics endpoint: ${PENIN_METRICS_BIND_HOST:-127.0.0.1}:${PENIN_METRICS_PORT:-8000}"

# Graceful shutdown handler
trap 'echo "🛑 Received shutdown signal, gracefully stopping..."; kill -TERM $PID; wait $PID' SIGTERM SIGINT

# Start the application
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌟 PENIN-Ω is ready"
echo ""

# Execute the main command
exec "$@" &
PID=$!
wait $PID

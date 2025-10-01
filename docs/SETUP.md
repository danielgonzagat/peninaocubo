# PENIN-Ω Setup Guide

This guide will help you set up and run the PENIN-Ω system.

## Prerequisites

- **Python**: 3.11 or higher
- **OS**: Linux, macOS, or Windows with WSL
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Disk**: ~2GB for dependencies

## Installation Methods

### Method 1: Standard Installation (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd peninaocubo

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install core package
pip install -e .

# 4. Install with full features (LLM providers, observability)
pip install -e ".[full]"

# 5. Install development tools (optional)
pip install -e ".[dev]"
```

### Method 2: From requirements.txt

```bash
# For users who prefer requirements.txt
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Method 3: Docker (Coming Soon)

```bash
docker-compose up -d
```

## Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

### Required Environment Variables

```bash
# LLM Provider API Keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
XAI_API_KEY=...
MISTRAL_API_KEY=...

# Optional: Observability
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Optional: Redis for caching
REDIS_HOST=localhost
REDIS_PORT=6379

# Optional: Budget limits
PENIN_ROUTER__DAILY_BUDGET=5.0  # USD
```

## Verifying Installation

```bash
# Check Python version
python --version  # Should be 3.11+

# Verify package installation
python -c "from penin.cli import main; print('✓ Installation successful')"

# Check available commands
penin --help
```

## Running Services

### Individual Services

Start each service in a separate terminal:

```bash
# Terminal 1: Σ-Guard (Security gates)
penin guard

# Terminal 2: SR-Ω∞ (Self-reflection)
penin sr

# Terminal 3: Ω-META (Master orchestrator)
penin meta

# Terminal 4: ACFA League (Deployment management)
penin league
```

### All Services at Once

```bash
# Using the demo script
python demo/run_demo.py

# Or using process manager (coming soon)
penin start-all
```

## Quick Start Examples

### Example 1: Basic Cycle Execution

```python
from penin.engine.master_equation import MasterEquation
from penin.config import PeninConfig

config = PeninConfig()
engine = MasterEquation(config)

# Run a single evolution cycle
result = await engine.cycle()
print(f"Alpha: {result.alpha}, CAOS+: {result.caos}")
```

### Example 2: LLM Router

```python
from penin.router import CostAwareRouter
from penin.config import RouterConfig

router = CostAwareRouter(RouterConfig(daily_budget=5.0))

# Route request to best provider
response = await router.route(
    prompt="Explain quantum computing",
    requirements={"quality": 0.8, "max_cost": 0.01}
)
```

### Example 3: WORM Ledger

```python
from penin.ledger.worm_ledger import WORMLedger

ledger = WORMLedger("./ledger.db")

# Write audit event
ledger.append({
    "event_type": "PROMOTE_ATTEST",
    "alpha": 0.95,
    "hash_pre": "abc123...",
    "hash_post": "def456..."
})

# Read history
events = ledger.read_all()
```

## Running Tests

```bash
# Run all tests
./scripts/run_tests.sh

# Run with coverage
./scripts/run_tests.sh --coverage

# Run specific test
./scripts/run_tests.sh -t tests/test_caos.py

# Run only unit tests
./scripts/run_tests.sh -m unit
```

## Development Setup

For contributors:

```bash
# Install with dev dependencies
pip install -e ".[dev,full]"

# Install pre-commit hooks
pre-commit install

# Run linters
ruff check .
black --check .
mypy penin/

# Auto-format code
black .
ruff check --fix .
```

## Troubleshooting

### Import Errors

```bash
# Ensure package is installed
pip install -e .

# Check PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH
```

### Missing Dependencies

```bash
# Install specific missing package
pip install <package-name>

# Reinstall all dependencies
pip install -e ".[full]" --force-reinstall
```

### Port Already in Use

```bash
# Find process using port
lsof -i :8010

# Kill process
kill <PID>

# Or use different port
penin meta --port 8020
```

### Performance Issues

```bash
# Enable performance monitoring
export PENIN_PERF_MONITORING=true

# Reduce concurrency
export PENIN_MAX_WORKERS=2

# Use Redis for caching
export PENIN_CACHE_BACKEND=redis
```

## Observability

### Prometheus Metrics

Access metrics at: http://localhost:8010/metrics

Key metrics:
- `penin_alpha` - Current α value
- `penin_caos` - CAOS+ score
- `penin_sr` - Self-reflection score
- `penin_decisions_total` - Decision counter

### Logs

Structured JSON logs are written to:
- Console (stdout/stderr)
- `./logs/penin.log` (if file logging enabled)

Configure logging:

```bash
export PENIN_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
export PENIN_LOG_FORMAT=json  # json or text
```

### Health Checks

```bash
# Check all services
curl http://localhost:8010/health
curl http://localhost:8011/health
curl http://localhost:8012/health
curl http://localhost:8013/health
```

## Production Deployment

See [Operations Guide](operations/) for:
- Kubernetes deployment
- Docker Compose setup
- High availability configuration
- Backup and retention policies
- Security hardening

## Next Steps

1. **Read the [User Guide](index.md)** for detailed feature documentation
2. **Review [Examples](../examples/)** for common use cases
3. **Check [API Reference](api/)** for complete API documentation
4. **Join discussions** on GitHub for questions and support

## Getting Help

- **Documentation**: Browse `docs/` directory
- **Examples**: Check `examples/` directory
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions

---

**Last Updated**: October 2025  
**Maintainer**: PENIN-Ω Team

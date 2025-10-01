# PENIN-Ω — Lemniscata ∞̸ Auto-Evolution System

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**PENIN-Ω** is a self-evolving AI system implementing the Master Equation with CAOS+, SR-Ω∞, and L∞ aggregation for ethical, auditable, and production-ready machine learning operations.

## 🌟 Features

- **🧬 Auto-Evolution Engine**: Self-improving system using Master Equation with CAOS+ boost
- **🛡️ Σ-Guard**: Fail-closed security gates with non-compensatory validation
- **📊 SR-Ω∞ Service**: Self-reflection scoring with continuous assessment
- **🏆 ACFA League**: Shadow/Canary deployment orchestration with automatic rollback
- **📝 WORM Ledger**: Write-Once-Read-Many audit trail with Merkle chain
- **🔍 Ethics Metrics**: ECE, bias ratios, and fairness scores with attestation
- **🔌 Multi-Provider Router**: Cost-aware LLM routing (OpenAI, Anthropic, Gemini, Grok, Mistral)
- **📈 Observability**: Prometheus metrics, structured logging, and distributed tracing
- **🧪 Research Plugins**: Optional NextPy, NASLib, Mammoth, SymbolicAI integration

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd <repository-name>

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[full]"  # Full installation with all features
# OR
pip install -e .          # Core installation only
```

### Basic Usage

```python
from penin.cli import main

# Run PENIN-Ω CLI
main()
```

### Running Services

```bash
# Start individual services
penin guard   # Σ-Guard on :8011
penin sr      # SR-Ω∞ on :8012
penin meta    # Ω-META on :8010
penin league  # ACFA League on :8013

# Run demo
python demo/run_demo.py
```

## 📦 Project Structure

```
.
├── penin/                  # Main package
│   ├── engine/            # Core evolution engine (CAOS+, Fibonacci, Master Equation)
│   ├── omega/             # Omega modules (ACFA, ethics, scoring, tuning)
│   ├── guard/             # Σ-Guard service
│   ├── sr/                # SR-Ω∞ service
│   ├── meta/              # Ω-META orchestrator
│   ├── league/            # ACFA League (shadow/canary)
│   ├── ledger/            # WORM ledger implementation
│   ├── providers/         # LLM provider adapters
│   ├── router.py          # Cost-aware LLM router
│   ├── cli/               # Command-line interface
│   └── ...
├── tests/                 # Test suite
├── examples/              # Usage examples
├── docs/                  # Documentation
├── deploy/                # Deployment configurations
├── scripts/               # Utility scripts
├── pyproject.toml         # Project configuration
└── README.md             # This file
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=penin tests/

# Run specific test suite
pytest tests/test_caos.py -v
```

## 📖 Documentation

- **[User Guide](docs/index.md)**: Comprehensive usage documentation
- **[API Reference](docs/api/)**: Detailed API documentation
- **[Operations Guide](docs/operations/)**: Deployment and operations
- **[Archive](docs/archive/)**: Historical documentation and audit reports

## 🔧 Configuration

Configuration is managed through Pydantic settings with environment variable support:

```python
from penin.config import PeninConfig

config = PeninConfig(
    evolution={"seed": 12345},
    fibonacci={"enabled": True},
    caos_plus={"max_boost": 0.05}
)
```

Environment variables:
```bash
export PENIN_EVOLUTION__SEED=12345
export PENIN_CAOS_PLUS__MAX_BOOST=0.05
```

## 🛡️ Security Features

- **Fail-Closed Design**: All gates default to safe state on errors
- **Deterministic Replay**: Full reproducibility with seed-based RNG
- **WORM Audit Trail**: Tamper-proof event logging with hash chains
- **Attestation**: Cryptographic proofs for all promotions
- **Budget Control**: Cost tracking and enforcement for LLM calls

## 🌐 API Endpoints

### Ω-META (:8010)
- `GET /health` - Health check
- `POST /api/v1/cycle` - Execute Master Equation cycle
- `GET /api/v1/status` - System status

### Σ-Guard (:8011)
- `POST /validate` - Validate promotion gates
- `GET /health` - Service health

### SR-Ω∞ (:8012)
- `POST /reflect` - Self-reflection scoring
- `GET /history` - Reflection history

### ACFA League (:8013)
- `POST /deploy` - Deploy challenger model
- `GET /status` - League status
- `POST /promote` - Promote canary to champion

## 📊 Metrics

Prometheus metrics available at `:8010/metrics`:

- `penin_alpha` - Current α_t^Ω value
- `penin_delta_linf` - Change in L∞ score
- `penin_caos` - CAOS+ score
- `penin_sr` - Self-reflection score
- `penin_decisions_total` - Decision counter by type
- `penin_gate_fail_total` - Gate failure counter
- `penin_cycle_duration_seconds` - Cycle execution time

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linters
ruff check .
black --check .
mypy penin/

# Format code
black .
ruff check --fix .
```

## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- PENIN-Ω architecture inspired by evolutionary computation and fail-safe engineering
- Built with FastAPI, Pydantic, and modern Python tooling
- Special thanks to the open-source community

## 📧 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check existing documentation in `docs/`
- Review archived audit reports in `docs/archive/`

## 🗺️ Roadmap

- [ ] Enhanced multi-model ensemble support
- [ ] Kubernetes operator for production deployment
- [ ] Real-time dashboard with WebSocket updates
- [ ] Advanced policy engine with OPA/Rego
- [ ] Extended provider support (Claude, Cohere, etc.)
- [ ] Performance optimization for high-throughput scenarios

---

**Version:** 0.8.0  
**Status:** Production Ready  
**Last Updated:** October 2025

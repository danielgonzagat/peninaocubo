# PENIN-Ω Documentation

Welcome to the PENIN-Ω documentation! This guide covers everything you need to know about the auto-evolution system.

## 📚 Documentation Structure

### Getting Started
- **[Setup Guide](SETUP.md)** - Installation and configuration
- **[Quick Start](#quick-start)** - Get running in 5 minutes
- **[Architecture Overview](#architecture)** - System design and components

### Core Concepts
- **[Master Equation](#master-equation)** - Core evolution algorithm
- **[CAOS+ System](#caos)** - Chaos-based exploration and promotion
- **[SR-Ω∞ Service](#sr)** - Self-reflection scoring
- **[L∞ Aggregation](#linf)** - Non-compensatory scoring
- **[WORM Ledger](#worm)** - Audit trail and attestation

### Features
- **[LLM Router](#router)** - Cost-aware provider selection
- **[Σ-Guard](#guard)** - Security gates and validation
- **[ACFA League](#league)** - Shadow/Canary deployment
- **[Ethics Metrics](#ethics)** - Fairness and bias measurement
- **[Observability](#observability)** - Monitoring and logging

### Operations
- **[Deployment](operations/)** - Production deployment guides
- **[Monitoring](#monitoring)** - Metrics and alerting
- **[Troubleshooting](#troubleshooting)** - Common issues and solutions

### Development
- **[Contributing](../CONTRIBUTING.md)** - How to contribute
- **[Testing](#testing)** - Test suite and coverage
- **[API Reference](#api)** - Complete API documentation

---

## Quick Start

### Installation

```bash
# Clone and install
git clone <repository-url>
cd peninaocubo
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[full]"
```

### Run Demo

```bash
# Start all services
python demo/run_demo.py
```

### Basic Usage

```python
from penin.cli import main

# Run CLI
main()
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────┐
│                      PENIN-Ω System                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  │  Ω-META  │───▶│ Σ-Guard  │───▶│  SR-Ω∞   │         │
│  │  :8010   │    │  :8011   │    │  :8012   │         │
│  └─────┬────┘    └──────────┘    └──────────┘         │
│        │                                                 │
│        ▼                                                 │
│  ┌─────────────┐         ┌────────────────┐            │
│  │ Master Eq.  │────────▶│  WORM Ledger   │            │
│  │ CAOS+ / Fib │         │  (Audit Trail) │            │
│  └─────────────┘         └────────────────┘            │
│        │                                                 │
│        ▼                                                 │
│  ┌─────────────────────────────────────┐               │
│  │        ACFA League (:8013)          │               │
│  │  ┌─────────┐  ┌────────┐  ┌──────┐ │               │
│  │  │Champion │  │ Canary │  │Shadow│ │               │
│  │  └─────────┘  └────────┘  └──────┘ │               │
│  └─────────────────────────────────────┘               │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Core Components

1. **Ω-META Service** (:8010)
   - Master orchestrator
   - Coordinates evolution cycles
   - Exposes REST API

2. **Σ-Guard** (:8011)
   - Security validation gates
   - Non-compensatory requirements
   - Fail-closed design

3. **SR-Ω∞** (:8012)
   - Self-reflection scoring
   - Continuous assessment
   - Historical tracking

4. **ACFA League** (:8013)
   - Shadow/Canary deployment
   - Automatic promotion
   - Rollback capabilities

---

## Master Equation

The Master Equation is the core of PENIN-Ω's auto-evolution:

```
α_{t+1}^Ω = α_t^Ω + η · ΔL∞ · CAOS⁺ · SR · G · OCI
```

Where:
- **α^Ω**: Evolution parameter (0 to 1)
- **η**: Learning rate
- **ΔL∞**: Change in L∞ aggregated score
- **CAOS⁺**: Chaos exploration factor with boost
- **SR**: Self-reflection score
- **G**: Global coherence score
- **OCI**: Operational coherence index

### Key Properties

1. **Deterministic**: Same seed → same results
2. **Auditable**: Every decision logged to WORM
3. **Fail-Closed**: Defaults to safe state on errors
4. **Non-Compensatory**: All gates must pass

---

## CAOS+ System {#caos}

CAOS+ (Chaos-Augmented Optimization System) provides:

### Features

- **Exploration Boost**: Fibonacci-based enhancement (max 5%)
- **EWMA Smoothing**: Stable pattern detection
- **Configurable**: Adjustable parameters
- **Audited**: All boosts logged

### Configuration

```python
config = {
    "caos_plus": {
        "max_boost": 0.05,        # 5% maximum boost
        "ewma_alpha": 0.2,        # Smoothing factor
        "min_stability_cycles": 5  # Cycles before boost
    }
}
```

---

## SR-Ω∞ Service {#sr}

Self-reflection scoring provides continuous quality assessment.

### Endpoints

- `POST /reflect` - Calculate SR score
- `GET /history` - Get reflection history
- `GET /health` - Service health check

### Usage

```python
from penin.sr.sr_service import SRService

sr = SRService()
score = await sr.reflect(context={
    "alpha": 0.95,
    "caos": 1.2,
    "recent_decisions": [...]
})
```

---

## L∞ Aggregation {#linf}

Non-compensatory harmonic aggregation ensures all metrics matter:

```python
L∞ = H([usability, safety, coherence, learning])
```

Where H is the harmonic mean - poor performance in any dimension cannot be compensated by excellence in others.

---

## WORM Ledger {#worm}

Write-Once-Read-Many audit trail with cryptographic proofs.

### Features

- **Immutable**: Events cannot be modified
- **Merkle Chain**: Hash-linked for integrity
- **Indexed**: Fast queries by event type
- **SQLite**: Lightweight and embedded

### Usage

```python
from penin.ledger.worm_ledger import WORMLedger

ledger = WORMLedger("./audit.db")

# Append event
ledger.append({
    "event_type": "PROMOTE_ATTEST",
    "alpha": 0.95,
    "timestamp": "2025-10-01T12:00:00Z"
})

# Query events
events = ledger.query(event_type="PROMOTE_ATTEST")
```

---

## LLM Router {#router}

Cost-aware routing across multiple LLM providers.

### Supported Providers

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Google (Gemini)
- xAI (Grok)
- Mistral

### Features

- **Multi-Factor Scoring**: Quality (40%) + Latency (30%) + Cost (30%)
- **Budget Control**: Daily spending limits
- **Usage Tracking**: Tokens, requests, costs
- **Fail-Closed**: Errors if budget exceeded

### Configuration

```python
from penin.router import CostAwareRouter
from penin.config import RouterConfig

router = CostAwareRouter(RouterConfig(
    daily_budget=5.0,  # $5 USD per day
    quality_weight=0.4,
    latency_weight=0.3,
    cost_weight=0.3
))
```

---

## Σ-Guard {#guard}

Security validation with non-compensatory gates.

### Gates

1. **CAOS+ Gate**: Must be ≥ 1.0
2. **SR Gate**: Must be ≥ 0.80
3. **ΔL∞ Gate**: Must be ≥ 0.01
4. **Allow Gate**: Must be true

### All gates must pass - there is no compensation!

---

## ACFA League {#league}

Advanced Canary/Fast-fail Alliance for safe deployments.

### Deployment Stages

1. **Shadow** (0% traffic)
   - Collect metrics
   - No user impact
   - Duration: configurable (default 5min)

2. **Canary** (1-5% traffic)
   - Limited user exposure
   - Automatic rollback on errors
   - Duration: configurable (default 10min)

3. **Champion** (100% traffic)
   - Promoted after passing gates
   - Becomes new baseline

---

## Ethics Metrics {#ethics}

Automated fairness and bias measurement.

### Metrics

1. **ECE** (Expected Calibration Error)
   - Measures prediction calibration
   - Lower is better

2. **ρ_bias** (Bias Ratio)
   - Group disparity measurement
   - Closer to 1.0 is fairer

3. **Fairness Score**
   - Demographic parity
   - Equalized odds

### Usage

```python
from penin.omega.ethics_metrics import compute_ethics_metrics

metrics = compute_ethics_metrics(
    predictions=predictions,
    labels=labels,
    protected_groups=groups
)
```

---

## Observability

### Prometheus Metrics

Available at `:8010/metrics`:

```
penin_alpha{service="omega_meta"} 0.95
penin_caos{service="omega_meta"} 1.15
penin_sr{service="sr_infinity"} 0.88
penin_decisions_total{type="promotion"} 42
```

### Structured Logging

JSON logs with trace IDs:

```json
{
  "timestamp": "2025-10-01T12:00:00.000Z",
  "level": "INFO",
  "trace_id": "abc-123-def",
  "event": "cycle_complete",
  "alpha": 0.95,
  "duration_ms": 125
}
```

---

## Testing

### Run Tests

```bash
# All tests
./scripts/run_tests.sh

# With coverage
./scripts/run_tests.sh --coverage

# Specific test
./scripts/run_tests.sh -t tests/test_caos.py
```

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **System Tests**: End-to-end scenarios

---

## Monitoring

### Health Checks

```bash
curl http://localhost:8010/health  # Ω-META
curl http://localhost:8011/health  # Σ-Guard
curl http://localhost:8012/health  # SR-Ω∞
curl http://localhost:8013/health  # ACFA League
```

### Alerting

Configure alerts in `deploy/prometheus/penin_alerts.yml`

---

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   lsof -i :8010
   kill <PID>
   ```

2. **Import errors**
   ```bash
   export PYTHONPATH=$PWD:$PYTHONPATH
   pip install -e .
   ```

3. **Missing dependencies**
   ```bash
   pip install -e ".[full]"
   ```

See [SETUP.md](SETUP.md#troubleshooting) for more details.

---

## API Reference {#api}

Complete API documentation coming soon in separate files:
- `api/omega_meta.md` - Ω-META API
- `api/sigma_guard.md` - Σ-Guard API
- `api/sr_infinity.md` - SR-Ω∞ API
- `api/acfa_league.md` - ACFA League API

---

## Additional Resources

- **[Changelog](../CHANGELOG.md)** - Version history
- **[Contributing](../CONTRIBUTING.md)** - Contribution guidelines
- **[License](../LICENSE)** - Apache 2.0
- **[Archive](archive/)** - Historical documentation

---

**Questions?** Open an issue on GitHub or check the discussions!

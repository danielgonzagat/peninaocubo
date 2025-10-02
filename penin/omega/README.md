# Omega - High-Level Integration APIs

**Purpose**: Pre-integrated workflows combining multiple PENIN-Ω components  
**Layer**: 4 (High-Level Integration)  
**Size**: ~7,300 lines across 23 files  

---

## 📖 Overview

The `omega/` module provides **high-level, pre-configured APIs** that combine multiple lower-level components. Think of it as the "batteries included" layer.

**Use omega when**:
- You want simplified APIs (don't want to wire components)
- You need combined metrics (e.g., ethics + SR + scoring in one call)
- You're building applications (not libraries)

**Don't use omega when**:
- You need fine-grained control → use `penin.math`, `penin.core`
- You're building libraries → depend on lower layers
- You need REST APIs → use service modules (`penin.sr`, etc.)

---

## 🗂️ Key Modules

### Mathematical Components

#### `sr.py` (1,157 lines)
**SR-Ω∞ mathematical implementation** with multiple aggregation methods.

```python
from penin.omega.sr import compute_sr_omega, SRAggregationMethod

score = compute_sr_omega(
    awareness=0.92,
    ethics_ok=True,
    autocorrection=0.88,
    metacognition=0.85,
    method=SRAggregationMethod.HARMONIC
)
```

**When to use**: Need SR calculation with custom configuration  
**Alternative**: `penin.sr.sr_service.SRService` for REST API  
**Alternative**: `penin.math.sr_omega_infinity` for low-level math  

---

#### `scoring.py` (100 lines)
Quick scoring utilities.

```python
from penin.omega.scoring import quick_harmonic, quick_score_gate

score = quick_harmonic([0.9, 0.8, 0.95])  # → 0.874
passed = quick_score_gate(score, threshold=0.80)  # → True
```

**When to use**: Simple scoring calculations  
**Alternative**: `penin.math.linf` for L∞ aggregation  

---

### Ethics & Safety

#### `ethics_metrics.py` (958 lines)
**Integrated ethics scoring** with ΣEA/LO-14 and metrics calculation.

```python
from penin.omega.ethics_metrics import EthicsCalculator, EthicsGate

calculator = EthicsCalculator()
metrics = calculator.compute_all(
    privacy_score=0.98,
    consent_obtained=True,
    eco_impact_kwh=2.5
)

gate = EthicsGate()
result = gate.validate(metrics)
if not result.passed:
    print(f"Ethics violation: {result.violations}")
```

**When to use**: Combined ethics + metrics calculation  
**Alternative**: `penin.ethics.laws.EthicsValidator` for modular validation  
**Alternative**: `penin.ethics.validators` for specific validators  

---

#### `guards.py` (764 lines)
**Σ-Guard + IR→IC** integrated implementation.

```python
from penin.omega.guards import SigmaGuardIntegrated

guard = SigmaGuardIntegrated()
result = guard.validate_evolution(
    rho=0.92,
    ece=0.003,
    rho_bias=1.01,
    delta_linf=0.02,
    ethics_ok=True
)

if result.verdict == "promote":
    # Safe to promote
    pass
```

**When to use**: Guards with integrated ethics checking  
**Alternative**: `penin.guard.sigma_guard_complete.SigmaGuard` for standalone  

---

### Audit & Ledger

#### `ledger.py` (801 lines)
**SQLite-based WORM ledger** with Pydantic schemas.

```python
from penin.omega.ledger import WORMLedgerSQL

ledger = WORMLedgerSQL(db_path="./penin_ledger.db")
record_id = ledger.append(
    decision_id="evolution_001",
    linf_score=0.92,
    caos_plus=28.5,
    verdict="promote"
)

# Verify integrity
chain_valid = ledger.verify_chain()
```

**When to use**: Want SQL backend for ledger  
**Alternative**: `penin.ledger.worm_ledger_complete.WORMLedger` for file-based  
**Alternative**: `penin.ledger.pcag_generator` for PCAg generation  

---

### Evolution & ACFA

#### `acfa.py` (448 lines)
**ACFA League** (champion-challenger) implementation.

```python
from penin.omega.acfa import ACFALeague, ChallengerConfig

league = ACFALeague()
result = league.compete(
    champion_score=0.88,
    challenger_score=0.91,
    beta_min=0.01
)

if result.promote_challenger:
    league.promote_to_champion()
```

**When to use**: Running champion-challenger competitions  
**Alternative**: `penin.league.acfa_service` for REST API  

---

#### `runners.py` (544 lines)
Pre-configured execution runners.

```python
from penin.omega.runners import AutoEvolutionRunner

runner = AutoEvolutionRunner(config={...})
result = runner.run_cycle(
    n_iterations=5,
    budget_usd=10.0
)
```

**When to use**: Running full evolution cycles  
**Alternative**: `penin.pipelines.auto_evolution` for pipeline DSL  

---

### Performance & Evaluation

#### `evaluators.py` (443 lines)
Evaluation and validation utilities.

```python
from penin.omega.evaluators import PerformanceEvaluator

evaluator = PerformanceEvaluator()
metrics = evaluator.evaluate_model(
    model=challenger,
    test_data=test_set
)
```

---

#### `performance.py` (275 lines)
Performance tracking and metrics.

```python
from penin.omega.performance import PerformanceTracker

tracker = PerformanceTracker()
tracker.record_iteration(linf=0.92, caos=28.5)
stats = tracker.get_statistics()
```

---

### Utilities

#### `attestation.py` (430 lines)
Attestation and proof generation.

#### `vida_runner.py` (468 lines)
Vida/Morte gate execution.

#### `life_eq.py` (142 lines)
Life equation utilities.

#### `fractal.py` (115 lines)
Fractal coherence calculations.

#### `tuner.py` (102 lines)
Auto-tuning utilities.

#### `mutators.py` (108 lines)
Mutation generation helpers.

#### `api_metabolizer.py` (123 lines)
API transformation utilities.

#### `swarm.py` (45 lines)
Swarm intelligence helpers.

---

## 🎯 Usage Patterns

### Pattern 1: Quick Evaluation

```python
from penin.omega import (
    compute_sr_omega,
    quick_harmonic,
    EthicsCalculator
)

# SR score
sr = compute_sr_omega(0.9, True, 0.85, 0.82)

# Ethics check
ethics = EthicsCalculator()
eth_result = ethics.compute_all(privacy_score=0.98, consent_obtained=True)

# Combined
final_score = quick_harmonic([sr, eth_result.score])
```

### Pattern 2: Evolution Pipeline

```python
from penin.omega import ACFALeague, SigmaGuardIntegrated, WORMLedgerSQL

league = ACFALeague()
guard = SigmaGuardIntegrated()
ledger = WORMLedgerSQL()

# Compete
result = league.compete(champion_score=0.88, challenger_score=0.91)

# Validate
guard_result = guard.validate_evolution(...)
if guard_result.verdict == "promote":
    # Log and promote
    ledger.append(decision_id="evo_001", verdict="promote")
    league.promote_to_champion()
```

---

## 📊 Module Statistics

```
Total files:    23
Total lines:    ~7,300
Largest file:   sr.py (1,157 lines)
```

---

## 🔗 Related Modules

- **Theory**: `penin.equations` - Mathematical specs
- **Implementation**: `penin.math`, `penin.ethics` - Core implementations
- **Runtime**: `penin.core` - Orchestration
- **Services**: `penin.sr`, `penin.guard` - REST APIs

---

## 📚 Further Reading

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Overall hierarchy
- [equations/README.md](../equations/README.md) - Theory
- [math/README.md](../math/README.md) - Implementations
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Development guide

---

**Questions?** See parent [ARCHITECTURE.md](../ARCHITECTURE.md) or open a discussion.

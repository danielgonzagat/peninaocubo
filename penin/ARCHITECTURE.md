# 🏗️ PENIN-Ω Architecture

**Purpose**: Define clear module hierarchy and usage policies  
**Last Updated**: 2025-10-02  

---

## 📊 Module Hierarchy

PENIN-Ω follows a **layered architecture** from theory to practice:

```
┌─────────────────────────────────────────────┐
│  Layer 5: SERVICES (REST APIs)              │
│  sr/, guard/, meta/, league/                │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 4: OMEGA (High-Level Integration)    │
│  omega/ - Combines multiple components      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 3: CORE (Runtime Orchestration)      │
│  core/, engine/, pipelines/                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 2: MATH (Practical Implementations)  │
│  math/, ethics/, guard/, ledger/, rag/      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  Layer 1: EQUATIONS (Theory & Specs)        │
│  equations/ - Pure mathematical definitions │
└─────────────────────────────────────────────┘
```

---

## 📁 Module Guide

### Layer 1: EQUATIONS (Theory)

**Path**: `penin/equations/`  
**Purpose**: Pure mathematical definitions and specifications  
**When to use**: Understanding theory, reference implementation  
**Contents**:
- `penin_equation.py` - Master update equation
- `linf_meta.py` - L∞ aggregation theory
- `caos_plus.py` - CAOS+ spec
- `sr_omega_infinity.py` - SR-Ω∞ spec
- All 15 core equations

**Import Example**:
```python
from penin.equations.linf_meta import LInfMetaFunction  # Spec
```

---

### Layer 2: MATH (Implementations)

**Path**: `penin/math/`, `penin/ethics/`, `penin/guard/`, `penin/ledger/`, `penin/rag/`

**Purpose**: Production-ready implementations  
**When to use**: Direct calculations, building blocks  

#### penin/math/

Core mathematical computations:
- `linf.py` - L∞ scoring (canonical)
- `caos_plus_complete.py` - CAOS+ engine
- `sr_omega_infinity.py` - SR scoring
- `ir_ic_contractivity.py` - Risk contractivity
- `vida_morte_gates.py` - Life/Death gates

**Import Example**:
```python
from penin.math.linf import compute_linf_meta
from penin.math.caos_plus_complete import CAOSPlusEngine
```

#### penin/ethics/

Ethics validation and scoring:
- `laws.py` - 14 Leis Originárias (LO-01 to LO-14)
- `validators.py` - Ethics validators
- `agape.py` - Índice Agápe

**Import Example**:
```python
from penin.ethics.laws import EthicsValidator, OriginLaw
```

#### penin/guard/

Safety gates:
- `sigma_guard_complete.py` - Σ-Guard implementation (canonical)

**Import Example**:
```python
from penin.guard.sigma_guard_complete import SigmaGuard, GateMetrics
```

#### penin/ledger/

Audit trail:
- `worm_ledger_complete.py` - File-based WORM ledger (canonical)
- `pcag_generator.py` - Proof-Carrying Artifacts

**Import Example**:
```python
from penin.ledger.worm_ledger_complete import WORMLedger
from penin.ledger.pcag_generator import generate_proof_artifact
```

#### penin/rag/

Knowledge retrieval:
- `retriever.py` - Self-RAG (BM25 + hybrid)

**Import Example**:
```python
from penin.rag.retriever import HybridRetriever
```

---

### Layer 3: CORE (Runtime)

**Path**: `penin/core/`, `penin/engine/`, `penin/pipelines/`

**Purpose**: Orchestration and execution  
**When to use**: Running full systems, workflows  

#### penin/core/

Runtime orchestration:
- `caos.py` - CAOS+ runtime engine (canonical)
- `orchestrator.py` - System orchestrator

**Import Example**:
```python
from penin.core.caos import CAOSPlusEngine, compute_caos_plus
```

#### penin/engine/

Execution engines:
- `master_equation.py` - Master update execution
- `auto_tuning.py` - Hyperparameter tuning

#### penin/pipelines/

Workflow pipelines:
- `auto_evolution.py` - Auto-evolution pipeline

---

### Layer 4: OMEGA (High-Level Integration)

**Path**: `penin/omega/`

**Purpose**: Pre-integrated workflows combining multiple components  
**When to use**:
- You want simplified, integrated APIs
- You need combined metrics (ethics + SR + scoring)
- You don't want to wire components yourself

**Key Modules**:

#### omega/sr.py (1,157 lines)
Mathematical SR-Ω∞ with multiple aggregation methods.  
**Use when**: Custom SR config with full control  
**Alternative**: `penin.sr.sr_service` for REST API

#### omega/ethics_metrics.py (958 lines)
Integrated ethics + metrics.  
**Use when**: Combined ethics scoring  
**Alternative**: `penin.ethics` for modular components

#### omega/ledger.py (801 lines)
SQLite-based WORM ledger.  
**Use when**: SQL backend for audit  
**Alternative**: `penin.ledger.worm_ledger_complete` for file-based

#### omega/guards.py (764 lines)
Σ-Guard + ethics integration.  
**Use when**: Integrated guards with ethics  
**Alternative**: `penin.guard.sigma_guard_complete` for standalone

#### omega/acfa.py
ACFA League (champion-challenger).

#### omega/runners.py
Pre-configured execution runners.

**Import Example**:
```python
from penin.omega.sr import compute_sr_omega  # High-level
from penin.omega.ethics_metrics import EthicsCalculator
```

---

### Layer 5: SERVICES (APIs)

**Path**: `penin/sr/`, `penin/guard/`, `penin/meta/`, `penin/league/`

**Purpose**: REST APIs and service endpoints  
**When to use**: Microservices, distributed systems  

#### penin/sr/
- `sr_service.py` - SR-Ω∞ REST API

#### penin/guard/
- `sigma_guard_service.py` - Σ-Guard REST API

#### penin/meta/
- `omega_meta_service.py` - Ω-META REST API

#### penin/league/
- `acfa_service.py` - ACFA League REST API

**Import Example**:
```python
from penin.sr.sr_service import SRService
```

---

## 🎯 Usage Decision Tree

```
Need to...
├─ Understand theory/spec?
│  └─→ Use penin.equations
│
├─ Do direct calculations?
│  └─→ Use penin.math, penin.ethics, etc.
│
├─ Orchestrate full system?
│  └─→ Use penin.core, penin.engine
│
├─ Want pre-integrated APIs?
│  └─→ Use penin.omega
│
└─ Need REST APIs?
   └─→ Use service modules (sr/, guard/, etc.)
```

---

## 📝 Import Guidelines

### ✅ DO

```python
# Import from canonical sources
from penin.math.linf import compute_linf_meta
from penin.core.caos import CAOSPlusEngine
from penin.guard.sigma_guard_complete import SigmaGuard
```

### ⚠️ CONSIDER

```python
# High-level, pre-integrated
from penin.omega.sr import compute_sr_omega
```

### ❌ AVOID

```python
# Don't import from equations for production
from penin.equations.linf_meta import ...  # Use penin.math instead
```

---

## 🔄 Cross-Layer Dependencies

```
Services → Omega → Core → Math → Equations
   ↓         ↓      ↓       ↓
  Also can call Math/Core directly (skip Omega)
```

**Rule**: Can call lower layers, never higher layers.

---

## 📚 Further Reading

- `penin/omega/README.md` - Omega module guide
- `penin/math/README.md` - Math implementations
- `penin/equations/README.md` - Theory and specs
- `CONTRIBUTING.md` - Development guidelines

---

**Questions?** See module-specific READMEs or ask in discussions.

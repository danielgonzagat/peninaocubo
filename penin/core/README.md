# Core - Runtime Orchestration

**Layer**: 3 (Runtime)  
**Purpose**: System orchestration and execution  

## Key Modules

### `caos.py` (1,497 lines)
**Canonical CAOS+ runtime engine**.

```python
from penin.core.caos import CAOSPlusEngine, compute_caos_plus
score, details = compute_caos_plus(C=0.88, A=0.40, O=0.35, S=0.82, kappa=20.0)
```

This is the **primary implementation** for CAOS+.

### `orchestrator.py`
System-level orchestration.

### `artifacts.py`
Artifact management.

### `serialization.py`
State serialization/deserialization.

---

**See**: [ARCHITECTURE.md](../ARCHITECTURE.md)

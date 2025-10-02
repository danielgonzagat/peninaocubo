# Guard - Σ-Guard Safety Gates

**Layer**: 2-5 (Implementations + Services)  
**Purpose**: Fail-closed safety validation  

## Modules

### `sigma_guard_complete.py` (638 lines)
**Canonical Σ-Guard implementation**.
```python
from penin.guard.sigma_guard_complete import SigmaGuard, GateMetrics
guard = SigmaGuard()
result = guard.validate(metrics)
```

### `sigma_guard_service.py`
REST API for Σ-Guard.

**Alternative**: `penin.omega.guards` for integrated guards+ethics.

**See**: [ARCHITECTURE.md](../ARCHITECTURE.md)

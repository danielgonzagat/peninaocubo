# Ledger - WORM Audit Trail

**Layer**: 2 (Implementations)  
**Purpose**: Immutable audit logging  

## Modules

### `worm_ledger_complete.py` (673 lines)
**File-based WORM ledger** (canonical for file storage).
```python
from penin.ledger.worm_ledger_complete import WORMLedger
ledger = WORMLedger()
ledger.append(decision_id="evo_001", verdict="promote")
```

### `worm_ledger.py` (672 lines)
Alternative WORM implementation.

### `pcag_generator.py`
**Proof-Carrying Artifacts** generation.
```python
from penin.ledger.pcag_generator import generate_proof_artifact
artifact = generate_proof_artifact(decision_id="test", linf=0.92, ...)
```

### `hash_utils.py`
BLAKE2b hashing utilities.

**Alternative**: `penin.omega.ledger` for SQLite-based ledger.

**See**: [ARCHITECTURE.md](../ARCHITECTURE.md)

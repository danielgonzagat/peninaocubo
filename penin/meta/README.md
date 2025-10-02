# Meta - Ω-META Auto-Evolution

**Layer**: 2-5 (Implementations + Services)  
**Purpose**: Mutation generation and auto-evolution  

## Modules

### `mutation_generator.py`
Safe mutation generation.
```python
from penin.meta.mutation_generator import MutationGenerator
gen = MutationGenerator()
mutations = gen.generate_batch()
```

### `omega_meta_complete.py` (839 lines)
Complete Ω-META implementation.

### `omega_meta_service.py`
REST API for Ω-META.

### `guard_client.py`
Client for Σ-Guard service.

### `fusion_registry.py`
Fusion registry for experiments.

**See**: [ARCHITECTURE.md](../ARCHITECTURE.md)

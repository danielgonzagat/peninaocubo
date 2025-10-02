# Ethics - Ethical Framework & Validators

**Layer**: 2 (Implementations)  
**Purpose**: ΣEA/LO-14 implementation and validation  

## Modules

### `laws.py`
14 Leis Originárias (LO-01 to LO-14).
```python
from penin.ethics.laws import EthicsValidator, OriginLaw, DecisionContext
result = EthicsValidator.validate_all(context)
```

### `validators.py`
Specific validators for each law.

### `agape.py`
Índice Agápe implementation.

### `auditor.py`
Ethics audit utilities.

**See**: [ARCHITECTURE.md](../ARCHITECTURE.md)

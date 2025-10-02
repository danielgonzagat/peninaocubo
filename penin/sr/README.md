# SR - Self-Reflection Service

**Layer**: 5 (Services)  
**Purpose**: SR-Ω∞ REST API  

## Modules

### `sr_service.py` (531 lines)
SR-Ω∞ service with REST API.
```python
from penin.sr.sr_service import SRService
service = SRService()
await service.start()
```

**Alternatives**:
- `penin.omega.sr` - Mathematical implementation
- `penin.math.sr_omega_infinity` - Low-level math

**See**: [ARCHITECTURE.md](../ARCHITECTURE.md)

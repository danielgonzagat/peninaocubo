# Math - Mathematical Implementations

**Layer**: 2 (Practical Implementations)  
**Purpose**: Production-ready mathematical functions  

## Key Modules

### `linf.py` / `linf_complete.py`
L∞ meta-function (non-compensatory aggregation).
```python
from penin.math.linf import compute_linf_meta
score = compute_linf_meta(metrics=[0.9, 0.8, 0.95], weights=[0.4, 0.3, 0.3], cost=0.15)
```

### `caos_plus_complete.py`
CAOS+ engine (Consistency, Auto-evolution, Unknowable, Silence).
```python
from penin.math.caos_plus_complete import CAOSPlusEngine
engine = CAOSPlusEngine()
score = engine.compute(C=0.88, A=0.40, O=0.35, S=0.82)
```

### `sr_omega_infinity.py`
SR-Ω∞ scoring (metacognition).
```python
from penin.math.sr_omega_infinity import compute_sr_score
sr = compute_sr_score(awareness=0.92, ethics_ok=True, autocorr=0.88, metacog=0.85)
```

### `ir_ic_contractivity.py`
IR→IC risk contractivity (ρ < 1).

### `vida_morte_gates.py`
Life/Death gates (selection).

### `oci.py`
Organizational Closure Index.

### `penin_master_equation.py`
Master update equation.

---

**See**: [ARCHITECTURE.md](../ARCHITECTURE.md) for full hierarchy

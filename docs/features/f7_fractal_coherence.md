# F7: Fractal Coherence - Feature Documentation

## Overview

**Feature ID:** F7  
**Status:** ✅ Implemented (v0.9.0)  
**Difficulty:** Alto  
**Purpose:** Measure consistency of decision logic across different scales of abstraction

## Hypothesis

> "Uma decisão é fractalmente coerente se a lógica usada para tomá-la é consistente em diferentes 'escalas' de abstração."

A fractal coherence metric evaluates whether the system's policies and configurations remain consistent throughout the hierarchical decision tree, from high-level strategic decisions down to low-level operational parameters.

## Implementation

### Algorithm

Located in `penin/omega/fractal.py`:

```python
def fractal_coherence(root: OmegaNode) -> float:
    """
    Computes coherence score by:
    1. Traversing all nodes in decision tree
    2. Using root configuration as reference
    3. Computing similarity for each child node
    4. Returning average similarity (0.0-1.0)
    """
```

**Mathematical Definition:**

```
FC(T) = (1/N) Σ_i s(n_i, r)

where:
  s(n_i, r) = |C_r ∩ C_i| / |C_r|
  C_r = root configuration
  C_i = node i configuration
  N = total non-root nodes
```

### SR-Ω∞ Service Integration

**Endpoint:** `POST /sr/fractal_coherence`

**Request:**
```json
{
  "root_config": {"alpha": 0.001, "beta": 0.9, "kappa": 25},
  "depth": 3,
  "branching": 2
}
```

**Response:**
```json
{
  "fractal_coherence": 1.0,
  "tree_depth": 3,
  "branching_factor": 2,
  "total_nodes": 15,
  "metric_name": "penin_fractal_coherence"
}
```

### Prometheus Metric

**Metric Name:** `penin_fractal_coherence`  
**Type:** Gauge  
**Range:** [0.0, 1.0]  
**Endpoint:** `/metrics`

```
# HELP penin_fractal_coherence Fractal coherence score (0.0-1.0)
# TYPE penin_fractal_coherence gauge
penin_fractal_coherence 1.0
```

## Interpretation

| Score Range | Level | Interpretation | Action |
|-------------|-------|----------------|--------|
| FC ≥ 0.95 | Excelente | Perfect/near-perfect coherence | ✅ Proceed |
| 0.85 ≤ FC < 0.95 | Bom | Good coherence | ✅ Monitor |
| 0.70 ≤ FC < 0.85 | Aceitável | Acceptable coherence | ⚠️ Investigate |
| FC < 0.70 | Crítico | Significant divergence | 🚫 Alert/Block |

## Use Cases in IA³

### Phase 1: Solidification (v1.0)

1. **Σ-Guard Gate:** Add FC ≥ 0.85 requirement for promotion
2. **WORM Audit:** Log FC scores for all decisions
3. **Grafana Dashboard:** Real-time FC monitoring

### Phase 2: Federation (v2.0)

1. **Swarm Coherence:** Compare FC across distributed instances
2. **Policy Sync:** Detect and correct drift in federated systems
3. **Knowledge Market:** Verify coherence before knowledge exchange

### Phase 3: Transcendence (IA³)

1. **Auto-Architecture:** Validate self-modifications via FC
2. **Protocol Genesis:** Ensure protocol mutations maintain coherence
3. **Proto-Consciousness:** Track coherence in self-narrative

## Files Modified/Created

### Modified
- `penin/sr/sr_service.py` - Added fractal coherence endpoint and Prometheus metric
- `docs/architecture.md` - Added F7 section with theory and implementation

### Created
- `tests/test_fractal_coherence_f7.py` - 12 comprehensive tests
- `examples/demo_fractal_coherence_f7.py` - Interactive demonstration
- `docs/features/f7_fractal_coherence.md` - This documentation

## Testing

**Test Coverage:** 12 tests, all passing ✅

```bash
# Run F7 tests
pytest tests/test_fractal_coherence_f7.py -v

# Run demo
python examples/demo_fractal_coherence_f7.py
```

**Test Categories:**
- Algorithm correctness (8 tests)
- Service endpoints (3 tests)
- Prometheus integration (1 test)

## Examples

### Python API
```python
from penin.omega.fractal import build_fractal, fractal_coherence

# Create tree
tree = build_fractal({"alpha": 0.001}, depth=3, branching=2)

# Compute coherence
fc = fractal_coherence(tree)  # Returns 1.0 (perfect)
```

### REST API
```bash
# Query fractal coherence
curl -X POST http://localhost:8012/sr/fractal_coherence \
  -H "Content-Type: application/json" \
  -d '{
    "root_config": {"alpha": 0.001, "beta": 0.9},
    "depth": 2,
    "branching": 3
  }'
```

### Prometheus Query
```promql
# Current fractal coherence
penin_fractal_coherence

# Alert on low coherence
penin_fractal_coherence < 0.70
```

## Next Steps

1. **Integration:** Add FC to Σ-Guard promotion gates
2. **Monitoring:** Create Grafana dashboard for FC trends
3. **Automation:** Implement auto-correction when FC < threshold
4. **Research:** Explore adaptive thresholds based on context
5. **Federation:** Extend FC to distributed coherence metrics

## References

- **Theory:** `docs/architecture.md` § 5.0 F7: Coerência Fractal
- **Implementation:** `penin/omega/fractal.py` + `penin/sr/sr_service.py`
- **Tests:** `tests/test_fractal_coherence_f7.py`
- **Demo:** `examples/demo_fractal_coherence_f7.py`
- **Original Issue:** Feature: Implementar a base da Coerência Fractal (F7)

---

**Version:** 0.9.0  
**Date:** 2025-10-01  
**Status:** ✅ Complete and Tested  
**License:** Apache 2.0

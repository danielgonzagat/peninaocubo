# Quick Start: Using Optimized Master Equation

## TL;DR

The Master Equation cycle is now **67% faster** on average! Use it the same way as before - optimizations are automatic.

## Basic Usage

```python
from penin.math.penin_master_equation import (
    MasterEquationState,
    master_equation_cycle,
)
import numpy as np

# Create initial state
state = MasterEquationState(
    I=np.random.randn(100) * 0.5,
    n=0,
    alpha_n=0.0,
    caos_plus=1.5,
    sr_score=0.85,
    Linf=0.75,
)

# Define loss function (optimized version)
def loss_fn(state, evidence, policies):
    dot_product = np.dot(state, state)
    return dot_product + 0.01 * np.sqrt(dot_product)

# Run cycle (automatically uses optimized version)
new_state = master_equation_cycle(
    state=state,
    evidence=None,
    policies={},
    loss_fn=loss_fn,
    alpha_0=0.1,
    caos_plus=1.5,
    sr_score=0.85,
)
```

## Performance Tips

### ✅ DO: Write Efficient Loss Functions

```python
# Good: Reuse computations
def efficient_loss(state, evidence, policies):
    dot_product = np.dot(state, state)
    return dot_product + 0.01 * np.sqrt(dot_product)

# Avoid: Redundant calculations
def slow_loss(state, evidence, policies):
    return np.sum(state**2) + 0.01 * np.linalg.norm(state)
```

### ✅ DO: Use Vectorized Operations

```python
# Good: Vectorized
loss = np.dot(state, state)

# Avoid: Python loops
loss = sum(x**2 for x in state)
```

### ⚠️ AVOID: Creating Unnecessary Copies

The optimized implementation already handles this, but when writing custom functions:

```python
# Good: In-place when possible
np.clip(array, low, high, out=array)

# Less efficient: Creates new array
array = np.clip(array, low, high)
```

## Running Benchmarks

```bash
# Quick benchmark
python benchmarks/benchmark_master_equation.py

# With profiling
python benchmarks/benchmark_master_equation.py --profile

# Compare with baseline
python benchmarks/compare_results.py
```

## Performance Numbers

| State Size | Performance | Typical Use Case |
|------------|-------------|------------------|
| 10D | 0.028ms | Fast prototyping |
| 100D | 0.207ms | Production workloads |
| 1000D | 2.206ms | High-dimensional optimization |

## Backward Compatibility

✅ All existing code works without changes  
✅ Same API, same results  
✅ Just faster!

## Need More Speed?

For >10x improvements on large states, consider:

1. **JAX** (recommended for n > 500)
   ```python
   import jax
   gradient = jax.grad(loss_fn)(state)
   ```

2. **Parallel Evaluation** (good for multi-core)
   ```python
   # Custom parallel gradient estimation
   # See benchmarks/README.md for examples
   ```

## Questions?

- See `benchmarks/README.md` for detailed usage
- See `BENCHMARK_REPORT.md` for performance analysis
- See `OPTIMIZATION_SUMMARY.md` for technical details

---

**Note:** The optimizations maintain full numerical accuracy and pass all 33 existing tests.

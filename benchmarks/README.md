# PENIN-Ω Benchmarks

Performance benchmarking suite for the Master Equation cycle.

## Quick Start

### Run Benchmarks

```bash
# Run standard benchmarks
python benchmarks/benchmark_master_equation.py

# Run with profiling
python benchmarks/benchmark_master_equation.py --profile

# Run with memory profiling
python benchmarks/benchmark_master_equation.py --memory

# Save results
python benchmarks/benchmark_master_equation.py --save

# Create baseline for comparison
python benchmarks/benchmark_master_equation.py --save --baseline
```

### Compare Results

After running benchmarks as baseline and then again after optimizations:

```bash
python benchmarks/compare_results.py
```

### Analyze Performance

View detailed bottleneck analysis:

```bash
python benchmarks/analyze_performance.py
```

## Files

- `benchmark_master_equation.py`: Main benchmark suite
- `compare_results.py`: Compare baseline vs optimized results
- `analyze_performance.py`: Detailed performance analysis
- `optimized_loss.py`: Example optimized loss functions
- `BENCHMARK_REPORT.md`: Full performance optimization report
- `benchmark_baseline.json`: Baseline benchmark results
- `benchmark_results.json`: Current benchmark results

## Benchmark Scenarios

The suite includes benchmarks for:

1. **Small State (10D)**: Fast iteration scenarios
2. **Medium State (100D)**: Typical production workloads
3. **Large State (1000D)**: High-dimensional optimization
4. **With Constraints**: Projection and safety constraints

## Performance Targets

- **Target**: 30% improvement over baseline
- **Achieved**: 67.1% average improvement

## Optimization Techniques

### Applied Optimizations

1. ✅ Fast gradient estimation with pre-allocation
2. ✅ Optimized loss function computation
3. ✅ In-place array operations
4. ✅ Early returns for constraint checks
5. ✅ Reduced function call overhead

### Future Optimizations

For >10x performance gains:

- **JAX**: Automatic differentiation with GPU support
- **Parallel evaluation**: Multi-threaded gradient computation
- **Stochastic estimation**: Fewer evaluations for high dimensions

## Example: Custom Loss Function

```python
import numpy as np

def create_efficient_loss_fn():
    """Create an optimized loss function."""
    
    def loss_fn(state, evidence, policies):
        # Use dot product instead of sum + norm
        dot_product = np.dot(state, state)
        return dot_product + 0.01 * np.sqrt(dot_product)
    
    return loss_fn

# Use with master_equation_cycle
from penin.math.penin_master_equation import master_equation_cycle

loss_fn = create_efficient_loss_fn()
new_state = master_equation_cycle(
    state, evidence, policies, loss_fn,
    alpha_0=0.1, caos_plus=1.5, sr_score=0.85
)
```

## Profiling Tips

### CPU Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run your code
master_equation_cycle(...)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Memory Profiling

```python
import tracemalloc

tracemalloc.start()

# Run your code
master_equation_cycle(...)

current, peak = tracemalloc.get_traced_memory()
print(f"Peak memory: {peak / 1024:.1f} KB")
tracemalloc.stop()
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Run benchmarks
  run: |
    python benchmarks/benchmark_master_equation.py --save
    python benchmarks/compare_results.py
```

## Contributing

When optimizing:

1. Run baseline benchmarks first
2. Make surgical changes
3. Verify tests still pass
4. Run optimized benchmarks
5. Compare results
6. Document changes

## License

Same as parent project (PENIN-Ω).

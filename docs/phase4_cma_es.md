# Phase 4: The Forge of Hephaestus - CMA-ES Local Training

## Overview

Phase 4 introduces **CMA-ES (Covariance Matrix Adaptation Evolution Strategy)**, a state-of-the-art local optimization algorithm that cures the system's "Primitive Local Intelligence" by implementing sophisticated, adaptive search.

## What is CMA-ES?

CMA-ES is a powerful evolutionary algorithm that:
- Adapts its search strategy based on the optimization landscape
- Uses covariance matrix to model parameter correlations
- Is invariant to monotonic transformations of the objective function
- Excels at finding global optima in multi-modal landscapes
- Requires no derivative information (black-box optimization)

## Usage

### Basic Usage

```python
from penin.core import OmegaMetaOrchestrator, NumericVectorArtifact

# Initialize orchestrator with some artifacts
orchestrator = OmegaMetaOrchestrator()
orchestrator.add_knowledge("solution1", NumericVectorArtifact(vector=[1.0, 2.0, 3.0]))
orchestrator.add_knowledge("solution2", NumericVectorArtifact(vector=[0.5, 1.5, 2.5]))

# Define evaluation function (lower is better)
def evaluate_artifact(artifact: NumericVectorArtifact) -> float:
    return sum(x**2 for x in artifact.vector)  # Simple sphere function

# Run optimization
optimized = orchestrator._initiate_local_training(
    evaluate_artifact,
    max_generations=50,
    sigma0=0.5
)

# Add optimized solution back to knowledge base
orchestrator.add_knowledge("optimized", optimized)
```

### Advanced Configuration

```python
# Customize optimization parameters
optimized = orchestrator._initiate_local_training(
    evaluate_artifact,
    max_generations=100,     # More generations for harder problems
    sigma0=1.0,               # Larger initial step size for exploration
    popsize=20                # Custom population size (default: auto)
)

# Access rich metadata
print(f"Generations: {optimized.metadata['generations']}")
print(f"Final sigma: {optimized.metadata['final_sigma']}")
print(f"Started from: {optimized.metadata['starting_point']}")
```

## Method Signature

```python
def _initiate_local_training(
    self,
    evaluate_artifact: Callable[[NumericVectorArtifact], float],
    max_generations: int = 50,
    sigma0: float = 0.5,
    popsize: int | None = None,
) -> NumericVectorArtifact
```

### Parameters

- **evaluate_artifact**: Function that evaluates artifacts and returns a score (lower is better)
- **max_generations**: Maximum number of optimization generations (default: 50)
- **sigma0**: Initial standard deviation for exploration (default: 0.5)
- **popsize**: Population size per generation (default: None = auto-determined)

### Returns

A `NumericVectorArtifact` with:
- Optimized vector
- Metadata including method, generations, final_sigma, starting_point

### Raises

- **ValueError**: If knowledge_base is empty or contains no valid artifacts

## How It Works

1. **Smart Starting Point Selection**
   - Evaluates all artifacts in knowledge_base
   - Selects the best (lowest score) as starting point

2. **CMA-ES Optimization Loop**
   - Generates population of candidate solutions
   - Evaluates each candidate using provided function
   - Updates covariance matrix based on results
   - Adapts step size (sigma) automatically
   - Repeats for max_generations or until convergence

3. **Result Harvesting**
   - Extracts best solution found
   - Packages as NumericVectorArtifact
   - Includes rich metadata for tracking

4. **Integration**
   - Return optimized artifact
   - Main orchestrator integrates into knowledge_base

## Example: Ackley Function Optimization

The Ackley function is a challenging multi-modal benchmark:

```python
import numpy as np

def ackley(artifact: NumericVectorArtifact) -> float:
    x = np.array(artifact.vector)
    n = len(x)
    sum1 = np.sum(x**2)
    sum2 = np.sum(np.cos(2 * np.pi * x))
    return -20 * np.exp(-0.2 * np.sqrt(sum1 / n)) - np.exp(sum2 / n) + 20 + np.e

# Start from random point
orchestrator.add_knowledge("start", NumericVectorArtifact(vector=[3.0, 3.0, 3.0]))

# Optimize
optimized = orchestrator._initiate_local_training(ackley, max_generations=100, sigma0=1.0)

# Results typically show dramatic improvement:
# - Starting score: ~10-15
# - Final score: < 0.001
# - Distance to global optimum: < 0.0001
```

## Best Practices

### Choosing max_generations

- **Simple problems (convex)**: 20-50 generations
- **Medium complexity**: 50-100 generations
- **Hard multi-modal**: 100-200 generations
- **Very high dimensional**: May need 200+ generations

### Choosing sigma0

- **Well-scaled problems**: 0.5 (default)
- **Large search space**: 1.0 - 2.0
- **Fine-tuning**: 0.1 - 0.3
- **Rule of thumb**: About 1/4 of search space diameter

### Population Size

- Usually let CMA-ES auto-determine (popsize=None)
- Manual override only for:
  - Very noisy objectives (larger population)
  - Limited function evaluations (smaller population)
  - Debugging/testing (small fixed population)

### Evaluation Function Design

```python
# Good: Smooth, continuous, informative
def good_eval(artifact: NumericVectorArtifact) -> float:
    return sum(x**2 for x in artifact.vector)

# Avoid: Discontinuous, non-informative
def bad_eval(artifact: NumericVectorArtifact) -> float:
    return 0.0 if sum(artifact.vector) < 0 else 1.0  # Binary, no gradient info
```

## Performance Characteristics

- **Time Complexity**: O(generations × popsize × eval_time)
- **Space Complexity**: O(dimension²) for covariance matrix
- **Convergence Rate**: Linear to superlinear on many problems
- **Scalability**: Works well up to ~100 dimensions

## Comparison to Alternatives

| Algorithm | Local/Global | Derivative-Free | Adaptive | Multi-Modal |
|-----------|--------------|-----------------|----------|-------------|
| CMA-ES    | Local+       | ✓              | ✓        | ✓          |
| L-BFGS    | Local        | ✗              | Limited  | ✗          |
| Nelder-Mead| Local       | ✓              | ✗        | ✗          |
| PSO       | Global       | ✓              | Limited  | ✓          |
| Grid Search| Global      | ✓              | ✗        | ✓          |

CMA-ES strikes an excellent balance for the orchestrator's needs.

## References

- Hansen, N., & Ostermeier, A. (2001). "Completely Derandomized Self-Adaptation in Evolution Strategies"
- Hansen, N. (2016). "The CMA Evolution Strategy: A Tutorial"
- Python implementation: https://github.com/CMA-ES/pycma

## See Also

- [Phase 4 Demo Example](../examples/phase4_cma_es_demo.py)
- [Test Suite](../tests/core/test_cma_training.py)
- [Orchestrator API](../penin/core/orchestrator.py)

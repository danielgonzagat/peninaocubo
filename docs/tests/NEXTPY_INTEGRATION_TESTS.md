# NextPyModifier Integration Tests - Documentation

## Overview

This document provides comprehensive documentation for the NextPyModifier integration tests, explaining their purpose, structure, and how to use them as examples for integrating NextPyModifier with the evolutionary engine.

## Test File Location

`tests/integrations/test_nextpy_integration.py`

## Test Suite Structure

The test suite is organized into 6 main test classes, covering different aspects of integration:

### 1. TestNextPyModifierIntegrationWithOmegaMeta

**Purpose**: Validates integration between NextPyModifier and the Omega-Meta mutation system.

**Key Tests**:
- `test_mutation_structure_compatibility`: Ensures NextPyModifier mutations are compatible with Omega-Meta's `Mutation` dataclass
- `test_nextpy_mutation_format_matches_omega_meta`: Verifies mutation format includes all required fields for Omega-Meta consumption
- `test_nextpy_with_challenger_evaluation_workflow`: Demonstrates complete champion-challenger workflow with multiple mutations
- `test_nextpy_with_deployment_stages`: Tests mutations through progressive deployment stages (shadow → canary → rollout)
- `test_nextpy_mutation_rollback_scenario`: Validates rollback capability when mutations fail quality gates

**Example Usage**:
```python
# Generate mutation compatible with Omega-Meta
adapter = NextPyModifier()
adapter._initialized = True

mutation_result = await adapter.execute(
    "mutate",
    architecture_state={"model": "baseline_v1"},
    target_metrics={"accuracy": 0.9}
)

# Convert to Omega-Meta Mutation object
omega_mutation = Mutation(
    mutation_id=mutation_result["mutation_id"],
    mutation_type=MutationType.ARCHITECTURE_TWEAK,
    description="NextPy-generated enhancement",
    created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    expected_gain=mutation_result["expected_improvement"],
)
```

### 2. TestNextPyModifierWithWORMLedger

**Purpose**: Tests integration with the WORM (Write Once Read Many) ledger for complete auditability.

**Key Tests**:
- `test_nextpy_mutation_audit_trail`: Demonstrates how to log NextPyModifier operations to WORM ledger
- `test_nextpy_evolution_cycle_provenance`: Shows complete provenance tracking for an evolution cycle

**Example Usage**:
```python
from penin.ledger.worm_ledger_complete import create_worm_ledger

# Create ledger
ledger = create_worm_ledger("/path/to/ledger.jsonl")

# Generate mutation
mutation_result = await adapter.execute("mutate", state, metrics)

# Log to ledger
event = ledger.append(
    event_type="nextpy_mutation_generated",
    event_id=mutation_result["mutation_id"],
    payload={
        "mutation_type": mutation_result["mutation_type"],
        "expected_improvement": mutation_result["expected_improvement"],
        "timestamp": time.time(),
    }
)
```

### 3. TestNextPyModifierWithSigmaGuard

**Purpose**: Validates integration with Sigma Guard ethical gates for fail-closed safety.

**Key Tests**:
- `test_nextpy_mutation_passes_ethical_gates`: Tests mutations passing through ethical validation
- `test_nextpy_mutation_blocked_by_high_risk`: Ensures high-risk mutations are properly blocked

**Example Usage**:
```python
from penin.guard.sigma_guard_complete import SigmaGuard, GateMetrics

guard = SigmaGuard()

# Create metrics for validation
gate_metrics = GateMetrics(
    rho=0.98,         # Contractividade
    ece=0.005,        # Calibration error
    rho_bias=1.03,    # Bias ratio
    sr_score=0.85,    # Self-reflection score
    omega_g=0.90,     # Global coherence
    delta_linf=0.05,  # Improvement
    caos_plus=2.5,    # CAOS+ score
    cost_increase=0.05,
    kappa=20.0,
    consent=True,
    eco_ok=True,
)

# Validate
verdict = guard.validate(gate_metrics)
if verdict.passed:
    # Deploy mutation
    pass
else:
    # Rollback
    print(f"Failed gates: {verdict.reason}")
```

### 4. TestNextPyModifierEndToEndWorkflow

**Purpose**: Comprehensive end-to-end integration tests simulating real production workflows.

**Key Tests**:
- `test_complete_evolution_workflow`: Full workflow from generation → evaluation → gating → deployment
- `test_evolve_high_level_api_integration`: Tests the high-level `evolve()` API that combines all operations

**Example Usage**:
```python
# Complete evolution workflow in one call
result = await adapter.evolve(
    current_state={
        "model_name": "baseline_v1",
        "parameters": {"temperature": 0.7},
        "performance": {"accuracy": 0.75},
    },
    target_metrics={
        "accuracy": 0.85,
        "latency_ms": 100,
    }
)

# Result includes:
# - evolved_state: Mutated architecture
# - mutation: Mutation metadata
# - optimization: Prompt optimization results
# - compilation: Compiled artifact info
# - overall_improvement: Combined improvement factor
```

### 5. TestNextPyModifierConcurrencyAndRobustness

**Purpose**: Tests concurrent operations, error handling, and metrics tracking.

**Key Tests**:
- `test_concurrent_mutation_generation`: Validates handling of concurrent mutation requests
- `test_error_recovery_with_fail_open`: Tests graceful degradation with `fail_open=True`
- `test_error_propagation_with_fail_closed`: Tests strict error propagation with `fail_open=False`
- `test_metrics_tracking_across_operations`: Validates metrics are correctly tracked

**Example Usage**:
```python
# Configure for fail-open (graceful degradation)
config = NextPyConfig(fail_open=True)
adapter = NextPyModifier(config)
adapter._initialized = True

# This will return fallback instead of raising
result = await adapter.execute("invalid_operation", {})
assert result["status"] == "failed"
assert result["fallback"] is True

# Check metrics
metrics = adapter.get_metrics()
print(f"Success rate: {metrics['success_rate']:.2%}")
print(f"Average latency: {metrics['avg_latency_ms']:.2f}ms")
```

### 6. TestNextPyModifierUsageExamples

**Purpose**: Practical usage examples demonstrating real-world integration patterns.

**Key Tests**:
- `test_basic_usage_example`: Minimal example for single mutation-evaluation cycle
- `test_champion_challenger_pattern`: Champion-challenger deployment pattern
- `test_progressive_rollout_pattern`: Progressive rollout with monitoring
- `test_full_pipeline_with_observability`: Production-ready pipeline with full observability

**Example Usage - Champion-Challenger Pattern**:
```python
# Champion model (current production)
champion = {
    "model_id": "champion_v1",
    "accuracy": 0.85,
    "latency_ms": 100,
}

# Generate challengers
challengers = []
for i in range(3):
    mutation = await adapter.execute(
        "mutate",
        {"challenger_id": i, "baseline": champion},
        {"accuracy": 0.90, "latency_ms": 80},
    )
    challengers.append(mutation)

# Evaluate and select best
best = max(challengers, key=lambda x: x["expected_improvement"])

# Deploy best challenger if improvement threshold met
if best["expected_improvement"] > 0.05:
    # Deploy via progressive rollout
    deploy_progressive(best)
```

**Example Usage - Progressive Rollout**:
```python
rollout_stages = [
    {"name": "shadow", "traffic": 0.00, "duration": 300},
    {"name": "canary", "traffic": 0.05, "duration": 600},
    {"name": "rollout_10", "traffic": 0.10, "duration": 1800},
    {"name": "rollout_50", "traffic": 0.50, "duration": 3600},
    {"name": "full", "traffic": 1.00, "duration": 7200},
]

for stage in rollout_stages:
    # Deploy at this traffic level
    deploy_at_traffic(mutation, stage["traffic"])
    
    # Monitor for duration
    monitor_for(stage["duration"])
    
    # Check metrics - rollback if needed
    if metrics_degraded():
        rollback(mutation)
        break
```

## Running the Tests

### Run all NextPyModifier integration tests:
```bash
pytest tests/integrations/test_nextpy_integration.py -v
```

### Run specific test class:
```bash
pytest tests/integrations/test_nextpy_integration.py::TestNextPyModifierWithOmegaMeta -v
```

### Run specific test:
```bash
pytest tests/integrations/test_nextpy_integration.py::TestNextPyModifierUsageExamples::test_basic_usage_example -v
```

### Run with detailed output:
```bash
pytest tests/integrations/test_nextpy_integration.py -vv --tb=long
```

## Test Coverage Summary

The integration test suite provides comprehensive coverage of:

1. **Mutation Generation**: 5 tests
2. **WORM Ledger Integration**: 2 tests
3. **Sigma Guard Validation**: 2 tests
4. **End-to-End Workflows**: 2 tests
5. **Concurrency & Robustness**: 4 tests
6. **Usage Examples**: 4 tests

**Total**: 19 integration tests

## Key Integration Points Tested

### ✅ Omega-Meta Mutation System
- Mutation structure compatibility
- Champion-challenger workflows
- Deployment stage progression
- Rollback scenarios

### ✅ WORM Ledger
- Mutation audit trails
- Evolution cycle provenance
- Complete event logging

### ✅ Sigma Guard
- Ethical gate validation
- Risk-based blocking
- Non-compensatory validation

### ✅ Evolutionary Engine
- Complete evolution cycles
- Multi-stage evaluation
- Metric tracking
- Performance monitoring

### ✅ Error Handling
- Fail-open modes
- Fail-closed modes
- Concurrent operations
- Graceful degradation

## Best Practices

1. **Always Initialize**: Ensure `adapter._initialized = True` before testing
2. **Use Fail-Open for Testing**: Set `fail_open=True` in config for graceful test failures
3. **Track Metrics**: Use `get_metrics()` to monitor adapter health
4. **Audit Trail**: Log all operations to WORM ledger for compliance
5. **Validate Gates**: Always check Sigma Guard before deployment
6. **Progressive Rollout**: Use staged deployment for safety

## Real-World Integration Example

```python
"""Complete production-ready integration example"""
import asyncio
from penin.integrations.evolution.nextpy_ams import NextPyModifier, NextPyConfig
from penin.guard.sigma_guard_complete import SigmaGuard, GateMetrics
from penin.ledger.worm_ledger_complete import create_worm_ledger

async def evolve_with_full_pipeline():
    # Setup
    config = NextPyConfig(
        enable_ams=True,
        compile_prompts=True,
        safety_sandbox=True,
        rollback_on_failure=True,
        audit_trail=True,
    )
    adapter = NextPyModifier(config)
    adapter.initialize()
    
    guard = SigmaGuard()
    ledger = create_worm_ledger("/var/log/penin/evolution.jsonl")
    
    # Current state
    current_state = {
        "model_id": "production_v2",
        "parameters": {"temperature": 0.7, "max_tokens": 100},
        "performance": {"accuracy": 0.82, "latency_ms": 150},
    }
    
    # Target metrics
    target_metrics = {
        "accuracy": 0.90,
        "latency_ms": 100,
    }
    
    # Generate mutation
    mutation = await adapter.execute("mutate", current_state, target_metrics)
    
    # Log to ledger
    ledger.append(
        event_type="mutation_generated",
        event_id=mutation["mutation_id"],
        payload=mutation,
    )
    
    # Evaluate (simulated)
    gate_metrics = GateMetrics(
        rho=0.97, ece=0.008, rho_bias=1.04, sr_score=0.87,
        omega_g=0.92, delta_linf=0.08, caos_plus=2.7,
        cost_increase=0.03, kappa=22.0, consent=True, eco_ok=True,
    )
    
    # Validate with gates
    verdict = guard.validate(gate_metrics)
    
    if verdict.passed:
        # Log decision
        ledger.append(
            event_type="deployment_approved",
            event_id=f"{mutation['mutation_id']}_deploy",
            payload={"verdict": verdict.action, "reason": verdict.reason},
        )
        
        # Deploy via progressive rollout
        print(f"✅ Deploying mutation {mutation['mutation_id']}")
        # ... deployment code ...
    else:
        # Log rejection
        ledger.append(
            event_type="deployment_rejected",
            event_id=f"{mutation['mutation_id']}_reject",
            payload={"reason": verdict.reason, "failed_gates": verdict.reason},
        )
        print(f"❌ Mutation blocked: {verdict.reason}")

# Run
asyncio.run(evolve_with_full_pipeline())
```

## Conclusion

These integration tests provide a comprehensive validation suite for NextPyModifier's integration with the PENIN-Ω evolutionary engine. They serve both as test validation and as practical examples for implementing production-ready autonomous evolution systems.

For questions or issues, refer to:
- Main implementation: `penin/integrations/evolution/nextpy_ams.py`
- Omega-Meta system: `penin/meta/omega_meta_complete.py`
- WORM Ledger: `penin/ledger/worm_ledger_complete.py`
- Sigma Guard: `penin/guard/sigma_guard_complete.py`

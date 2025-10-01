# NextPyModifier Integration Tests

## Overview

This directory contains comprehensive integration tests for the NextPyModifier module, which is responsible for autonomous architecture modifications in the PENIN-Ω system.

## Test Files

### test_nextpy_integration.py

Comprehensive integration tests covering all aspects of NextPyModifier interaction with the evolutionary engine:

- **24 integration tests** covering:
  - CAOS+ Motor integration (3 tests)
  - SR-Ω∞ Self-Reflection integration (3 tests)
  - Ω-META Evolution Orchestration (3 tests)
  - Sigma Guard Validation (3 tests)
  - WORM Ledger Audit Trail (3 tests)
  - End-to-End Evolution (3 tests)
  - Performance Benchmarks (3 tests)
  - Usage Examples (3 tests)

### test_nextpy_ams.py

Unit tests for NextPyModifier adapter:

- Configuration tests
- Initialization tests
- Execution tests
- Status reporting tests

## Running the Tests

### All Integration Tests
```bash
pytest tests/integrations/test_nextpy_integration.py -v
```

### Specific Test Categories
```bash
# CAOS+ Motor integration
pytest tests/integrations/test_nextpy_integration.py::TestNextPyWithCAOS -v

# SR-Ω∞ integration
pytest tests/integrations/test_nextpy_integration.py::TestNextPyWithSR -v

# Ω-META orchestration
pytest tests/integrations/test_nextpy_integration.py::TestNextPyWithOmegaMeta -v

# Sigma Guard validation
pytest tests/integrations/test_nextpy_integration.py::TestNextPyWithSigmaGuard -v

# WORM Ledger audit
pytest tests/integrations/test_nextpy_integration.py::TestNextPyWithWORMLedger -v

# End-to-end tests
pytest tests/integrations/test_nextpy_integration.py::TestEndToEndEvolution -v

# Performance benchmarks
pytest tests/integrations/test_nextpy_integration.py::TestPerformanceBenchmarks -v
```

### With Markers
```bash
# Only integration tests
pytest tests/integrations/test_nextpy_integration.py -v -m integration

# Exclude slow tests
pytest tests/integrations/test_nextpy_integration.py -v -m "integration and not slow"
```

### With Coverage
```bash
pytest tests/integrations/test_nextpy_integration.py -v \
    --cov=penin.integrations.evolution \
    --cov-report=html \
    --cov-report=term-missing
```

## Test Results

All tests are passing:
- ✅ 24 integration tests
- ✅ 9 unit tests
- ✅ 0 failures
- ✅ Performance benchmarks within acceptable ranges

## Documentation

For detailed documentation on the integration tests, see:
- [NextPy Integration Tests Documentation](../../docs/tests/nextpy_integration_tests.md)

## Test Coverage

The tests provide comprehensive coverage of:

1. **Integration Points**:
   - CAOS+ Motor for consistency/autoevolution/incognoscível/silêncio scoring
   - SR-Ω∞ for self-reflection and metacognition
   - Ω-META for mutation orchestration and deployment
   - Sigma Guard for ethical validation (ΣEA/LO-14)
   - WORM Ledger for immutable audit trails

2. **Scenarios**:
   - Mutation generation and optimization
   - Champion-challenger evaluation
   - Shadow/canary/rollout deployment
   - Automatic rollback on failures
   - Evolution lineage tracking
   - Concurrent operations

3. **Performance**:
   - Mutation generation latency < 100ms
   - Evolution throughput > 1 cycle/second
   - Concurrent mutation handling

4. **Compliance**:
   - ΣEA/LO-14 ethical validation
   - Fail-closed design
   - Contractividade (IR→IC)
   - Lyapunov stability

## Usage Examples

The tests include three comprehensive usage examples:

### Example 1: Basic Usage
```python
config = NextPyConfig(enable_ams=True, compile_prompts=True)
adapter = NextPyModifier(config=config)
mutation = await adapter.execute("mutate", architecture_state)
```

### Example 2: Complete Pipeline
```python
evolution_result = await adapter.evolve(architecture, target_metrics)
caos_score = compute_caos_plus_exponential(c=0.85, a=0.75, o=0.60, s=0.90)
deploy_decision = mutation["risk_score"] < 0.3 and caos_score > 2.0
```

### Example 3: Rollback Scenario
```python
mutation = await adapter.execute("mutate", champion_state)
challenger_metrics = evaluate_metrics(challenger_state)
if challenger_metrics["accuracy"] < champion_metrics["accuracy"]:
    rollback_mutation(mutation)
```

## Contributing

When adding new integration tests:

1. Follow the existing test structure
2. Use descriptive test names
3. Add appropriate markers (`@pytest.mark.integration`, `@pytest.mark.slow`)
4. Include docstrings explaining what is being tested
5. Add usage examples for complex scenarios
6. Update documentation

## Related Documentation

- [NextPy AMS Module](../../penin/integrations/evolution/nextpy_ams.py)
- [CAOS+ Core](../../penin/core/caos.py)
- [SR-Ω∞ Service](../../penin/sr/sr_service.py)
- [Ω-META Complete](../../penin/meta/omega_meta_complete.py)
- [Sigma Guard](../../penin/guard/sigma_guard_complete.py)
- [WORM Ledger](../../penin/ledger/worm_ledger_complete.py)

## Contact

For questions or issues:
- [GitHub Issues](https://github.com/danielgonzagat/peninaocubo/issues)
- [GitHub Discussions](https://github.com/danielgonzagat/peninaocubo/discussions)

# Property-Based Testing for Σ-Guard

## Overview

This document describes the property-based tests for the Σ-Guard security gate using the `hypothesis` library. These tests validate the robustness of the fail-closed security gate by generating a wide range of inputs and ensuring that the system always behaves as expected.

## Test File

- **File**: `tests/test_sigma_guard_properties.py`
- **Library**: `hypothesis` (v6.0.0+)
- **Test Count**: 15 property-based tests across 6 test classes

## Test Categories

### 1. Fail-Closed Properties (`TestFailClosedProperties`)

Validates that the Σ-Guard maintains fail-closed behavior under all conditions.

#### Tests:
- **`test_verdict_structure_is_always_valid`** (200 examples)
  - Property: Verdict structure is always valid regardless of input
  - Validates: All required fields, proper types, hash proof generation
  
- **`test_fail_closed_never_promotes_on_violation`** (200 examples)
  - Property: System NEVER promotes when any gate fails
  - Validates: Fail-closed behavior, rollback action, verdict status
  
- **`test_single_failure_causes_rollback`** (200 examples)
  - Property: Single gate failure causes complete rollback (non-compensatory)
  - Validates: At least one failed gate, rollback action
  
- **`test_all_passing_gates_promotes`** (100 examples)
  - Property: When all gates pass, system promotes
  - Validates: All gates pass, promote action, positive aggregate score
  
- **`test_contractivity_violation_always_fails`** (100 examples)
  - Property: Contractivity violation (ρ >= 1.0) always causes failure
  - Validates: Specific gate failure behavior

### 2. Non-Compensatory Properties (`TestNonCompensatoryProperties`)

Validates that excellent metrics on some gates cannot compensate for failures on other gates.

#### Tests:
- **`test_excellent_metrics_cannot_compensate`** (100 examples)
  - Property: Excellent metrics on other gates cannot compensate for one failure
  - Tests: Each of the 10 gates independently
  - Validates: Non-compensatory design

### 3. Boundary Properties (`TestBoundaryProperties`)

Tests boundary conditions for all thresholds to ensure correct behavior at threshold edges.

#### Tests:
- **`test_rho_boundary_at_0_99`** (50 examples)
  - Property: ρ just below threshold passes, just above fails
  - Validates: Strict inequality handling (ρ < 0.99)
  
- **`test_ece_boundary_at_0_01`** (50 examples)
  - Property: ECE at boundary behaves correctly
  - Validates: Inequality handling (ECE ≤ 0.01)

### 4. Extreme Value Properties (`TestExtremeValueProperties`)

Tests handling of extreme and invalid values.

#### Tests:
- **`test_zero_values_handled_correctly`**
  - Property: Zero values are handled without errors
  - Validates: No crashes, proper verdict structure
  
- **`test_maximum_values_handled_correctly`**
  - Property: Maximum values are handled without errors
  - Validates: Handles large values gracefully
  
- **`test_nan_and_infinity_handled_safely`**
  - Property: NaN and infinity values don't crash the system
  - Validates: Graceful handling or appropriate exceptions

### 5. Idempotency Properties (`TestIdempotencyProperties`)

Tests determinism and idempotency of validation.

#### Tests:
- **`test_validation_is_deterministic`** (100 examples)
  - Property: Same metrics always produce same verdict
  - Validates: Deterministic behavior across multiple invocations
  
- **`test_multiple_guards_behave_identically`** (50 examples)
  - Property: Multiple guard instances with same config behave identically
  - Validates: Consistent behavior across instances

### 6. Gate Independence Properties (`TestGateIndependenceProperties`)

Tests that gates are evaluated independently.

#### Tests:
- **`test_all_gates_always_evaluated`** (100 examples)
  - Property: All 10 gates are always evaluated regardless of early failures
  - Validates: Complete gate evaluation, no short-circuiting
  
- **`test_each_gate_has_valid_result`** (100 examples)
  - Property: Each gate result is properly structured
  - Validates: Complete GateResult structure for all gates

## Running the Tests

### Run all property-based tests:
```bash
pytest tests/test_sigma_guard_properties.py -v
```

### Run with hypothesis statistics:
```bash
pytest tests/test_sigma_guard_properties.py -v --hypothesis-show-statistics
```

### Run specific test class:
```bash
pytest tests/test_sigma_guard_properties.py::TestFailClosedProperties -v
```

### Run with more examples (thorough testing):
```bash
pytest tests/test_sigma_guard_properties.py -v --hypothesis-seed=random
```

## Test Configuration

The tests use the following hypothesis settings:

- **max_examples**: Varies by test (50-200 examples)
- **deadline**: None (no time limit per example)
- **derandomize**: True (CI mode for reproducibility)
- **database**: None (CI mode)

## Key Properties Validated

1. **Fail-Closed Design**: System defaults to deny on any violation
2. **Non-Compensatory**: All gates must pass; excellence in one gate cannot compensate for failure in another
3. **Deterministic**: Same inputs always produce same outputs
4. **Complete Evaluation**: All gates evaluated even if early failures occur
5. **Robust**: Handles edge cases, extreme values, and invalid inputs gracefully
6. **Auditable**: All verdicts include complete gate results, reasons, and hash proofs

## Generated Input Strategies

### Valid Floats
Generates floats within specified ranges, excluding NaN and infinity:
```python
valid_floats(min_value=0.0, max_value=2.0)
```

### Valid GateMetrics
Generates GateMetrics with arbitrary valid values:
- Explores full input space
- Tests with random combinations of parameters

### Passing GateMetrics
Generates GateMetrics guaranteed to pass all gates:
- rho < 0.98
- ece ≤ 0.009
- rho_bias ≤ 1.04
- sr_score ≥ 0.81
- omega_g ≥ 0.86
- delta_linf ≥ 0.011
- cost_increase ≤ 0.09
- kappa ≥ 21.0
- consent = True
- eco_ok = True

### Failing GateMetrics
Generates GateMetrics with exactly one gate violation:
- Systematically tests each gate independently
- Returns metrics and the violated gate name

## Integration with CI/CD

The property-based tests are designed to run efficiently in CI/CD pipelines:

1. **Reproducible**: Uses CI mode with derandomization
2. **Fast**: Typical runtime < 2 seconds for full suite
3. **Thorough**: Tests 1000+ generated examples total
4. **Clear Failures**: Hypothesis provides minimal failing examples

## Benefits of Property-Based Testing

1. **Wider Coverage**: Tests thousands of input combinations automatically
2. **Edge Case Discovery**: Finds edge cases developers might miss
3. **Regression Prevention**: Catches regressions in boundary behavior
4. **Documentation**: Properties serve as executable specifications
5. **Confidence**: High confidence in robustness of fail-closed design

## References

- **Issue**: Testing: Validar o Σ-Guard com Testes de Propriedade
- **Implementation**: `penin/guard/sigma_guard_complete.py`
- **Hypothesis Documentation**: https://hypothesis.readthedocs.io/
- **PENIN-Ω Guide**: `PENIN_OMEGA_COMPLETE_EQUATIONS_GUIDE.md § 15`

## Future Enhancements

Potential additions to property-based tests:

1. **State Machine Testing**: Test sequences of validations
2. **Performance Properties**: Test that validation is fast (< 1ms)
3. **Memory Properties**: Test that validation doesn't leak memory
4. **Concurrency Properties**: Test thread-safety
5. **Integration Properties**: Test with mock WORM ledger

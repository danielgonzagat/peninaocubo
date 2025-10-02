"""
Property-Based Tests: Contratividade (IR→IC)
=============================================

Mathematical guarantee: ∀ k: H(L_ψ(k)) ≤ ρ·H(k), onde 0 < ρ < 1

Tests using Hypothesis for exhaustive validation.
"""

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Import contractivity operators
try:
    from penin.equations.ir_ic_contractive import lapidation_operator, risk_information
    from penin.iric.lpsi import apply_lpsi_operator, compute_risk_reduction_ratio
except ImportError:
    pytest.skip("IR→IC modules not available", allow_module_level=True)


class TestContractivityProperties:
    """Property-based tests for IR→IC contractivity guarantee."""

    @given(
        initial_risk=st.floats(min_value=0.01, max_value=1.0, allow_nan=False, allow_infinity=False)
    )
    @settings(max_examples=200, deadline=500)
    def test_lpsi_always_contractive(self, initial_risk: float):
        """
        Property: L_ψ operator always reduces risk.

        Mathematical form: ρ = H(L_ψ(k)) / H(k) < 1.0
        """
        try:
            # Apply lapidation operator
            evolved_risk = apply_lpsi_operator(initial_risk)

            # Compute contractivity ratio
            rho = evolved_risk / initial_risk

            # Critical assertion: ρ must be < 1.0 (strict contractivity)
            assert rho < 1.0, (
                f"Contractivity violated: ρ={rho:.6f} ≥ 1.0 "
                f"(initial={initial_risk:.6f}, evolved={evolved_risk:.6f})"
            )

            # Additional check: evolved risk must be strictly less
            assert evolved_risk < initial_risk, (
                f"Risk did not decrease: {evolved_risk:.6f} ≥ {initial_risk:.6f}"
            )

        except Exception as e:
            pytest.fail(f"L_ψ operator failed for risk={initial_risk:.6f}: {e}")

    @given(
        initial_risk=st.floats(min_value=0.1, max_value=0.9, allow_nan=False),
        iterations=st.integers(min_value=1, max_value=10),
    )
    @settings(max_examples=100, deadline=1000)
    def test_repeated_lpsi_monotonic_decrease(self, initial_risk: float, iterations: int):
        """
        Property: Repeated application of L_ψ monotonically decreases risk.

        ∀ t: risk(t+1) < risk(t)
        """
        risk = initial_risk
        previous_risks = [risk]

        for i in range(iterations):
            risk = apply_lpsi_operator(risk)

            # Check monotonic decrease
            assert risk < previous_risks[-1], (
                f"Iteration {i+1}: Risk increased or stayed same "
                f"({risk:.6f} ≥ {previous_risks[-1]:.6f})"
            )

            previous_risks.append(risk)

        # Check overall reduction
        final_reduction = initial_risk - risk
        assert final_reduction > 0, (
            f"No overall reduction: initial={initial_risk:.6f}, final={risk:.6f}"
        )

    @given(
        risk_a=st.floats(min_value=0.1, max_value=0.5, allow_nan=False),
        risk_b=st.floats(min_value=0.5, max_value=1.0, allow_nan=False),
    )
    @settings(max_examples=100, deadline=500)
    def test_lpsi_order_preserving(self, risk_a: float, risk_b: float):
        """
        Property: If risk_a < risk_b, then L_ψ(risk_a) < L_ψ(risk_b).

        Monotonicity of operator.
        """
        if risk_a >= risk_b:
            # Swap to ensure risk_a < risk_b
            risk_a, risk_b = risk_b, risk_a

        evolved_a = apply_lpsi_operator(risk_a)
        evolved_b = apply_lpsi_operator(risk_b)

        # Order must be preserved
        assert evolved_a < evolved_b, (
            f"Order not preserved: L_ψ({risk_a:.4f})={evolved_a:.4f} "
            f"≥ L_ψ({risk_b:.4f})={evolved_b:.4f}"
        )

    @given(
        initial_risk=st.floats(min_value=0.01, max_value=1.0, allow_nan=False)
    )
    @settings(max_examples=150, deadline=500)
    def test_rho_bounded(self, initial_risk: float):
        """
        Property: Contractivity ratio ρ is bounded: 0 < ρ < 1.
        """
        evolved_risk = apply_lpsi_operator(initial_risk)
        rho = compute_risk_reduction_ratio(initial_risk, evolved_risk)

        # Lower bound: ρ > 0 (risk can't become negative or zero)
        assert rho > 0, f"ρ={rho:.6f} ≤ 0 (risk became non-positive)"

        # Upper bound: ρ < 1 (strict contractivity)
        assert rho < 1.0, f"ρ={rho:.6f} ≥ 1.0 (no contraction)"

        # Typical range: 0.7 < ρ < 0.95 (sanity check)
        assert 0.5 < rho < 0.99, (
            f"ρ={rho:.6f} outside typical range [0.5, 0.99] "
            "(may indicate implementation issue)"
        )


class TestContractivityEdgeCases:
    """Edge case tests for contractivity."""

    def test_near_zero_risk(self):
        """Test behavior with very small initial risk."""
        initial_risk = 0.001
        evolved_risk = apply_lpsi_operator(initial_risk)
        rho = evolved_risk / initial_risk

        assert rho < 1.0, f"Contractivity failed for near-zero risk: ρ={rho}"
        assert evolved_risk > 0, "Risk became zero or negative"

    def test_high_risk(self):
        """Test behavior with very high initial risk."""
        initial_risk = 0.99
        evolved_risk = apply_lpsi_operator(initial_risk)
        rho = evolved_risk / initial_risk

        assert rho < 1.0, f"Contractivity failed for high risk: ρ={rho}"
        assert evolved_risk < initial_risk

    def test_typical_range(self):
        """Test typical risk range [0.3, 0.7]."""
        for risk in [0.3, 0.5, 0.7]:
            evolved = apply_lpsi_operator(risk)
            assert evolved < risk, f"No reduction for risk={risk}"


# Fixtures for integration with existing codebase

@pytest.fixture
def sample_risks():
    """Sample risk values for testing."""
    return [0.1, 0.3, 0.5, 0.7, 0.9]


def test_contractivity_on_samples(sample_risks):
    """Smoke test on sample values."""
    for risk in sample_risks:
        evolved = apply_lpsi_operator(risk)
        rho = evolved / risk
        assert rho < 1.0, f"Contractivity failed for risk={risk}: ρ={rho}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])

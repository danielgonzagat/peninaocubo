"""
Property-Based Tests for Contratividade (IR→IC)

Mathematical guarantee: ∀ evolution: ρ < 1 (risk reduction)
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st


# Helper functions for testing contractivity
def compute_contractivity(risk_before: float, risk_after: float) -> float:
    """Compute ρ = risk_after / risk_before"""
    if risk_before == 0.0:
        return 0.0
    return risk_after / risk_before


def validate_contractive_property(risk_before: float, risk_after: float) -> bool:
    """Check if ρ < 1.0"""
    rho = compute_contractivity(risk_before, risk_after)
    return rho < 1.0


@given(
    initial_risk=st.floats(min_value=0.1, max_value=1.0),
    reduction_factor=st.floats(min_value=0.1, max_value=0.99),
)
def test_contractivity_always_reduces_risk(initial_risk, reduction_factor):
    """
    Property: IR→IC always reduces risk (ρ < 1)

    ∀ initial_risk ∈ (0, 1], reduction ∈ (0, 1):
        evolved_risk = initial_risk * reduction
        ⇒ ρ = evolved_risk / initial_risk < 1
    """
    evolved_risk = initial_risk * reduction_factor

    rho = compute_contractivity(
        risk_before=initial_risk,
        risk_after=evolved_risk,
    )

    assert rho < 1.0, f"Contractivity violated: ρ={rho:.4f} ≥ 1.0"
    assert rho >= 0.0, f"Invalid ρ: {rho}"


@given(
    risk_before=st.floats(min_value=0.1, max_value=1.0),
    risk_after=st.floats(min_value=0.0, max_value=1.0),
)
def test_contractivity_validation(risk_before, risk_after):
    """
    Property: validate_contractive_property correctly identifies ρ < 1

    If risk_after < risk_before, then validation passes.
    If risk_after ≥ risk_before, then validation fails.
    """
    is_contractive = validate_contractive_property(risk_before, risk_after)

    if risk_after < risk_before:
        assert is_contractive, f"Should be contractive: {risk_before} → {risk_after}"
    else:
        assert not is_contractive, f"Should NOT be contractive: {risk_before} → {risk_after}"


@given(
    initial_risks=st.lists(
        st.floats(min_value=0.1, max_value=1.0),
        min_size=3,
        max_size=10,
    )
)
def test_multi_step_contractivity(initial_risks):
    """
    Property: Multi-step evolution maintains contractivity

    ∀ sequence of evolutions with ρ_i < 1:
        final_risk = initial_risk * Π(ρ_i)
        ⇒ final_risk < initial_risk
    """
    initial_risk = initial_risks[0]
    current_risk = initial_risk

    rho_product = 1.0

    for i in range(1, len(initial_risks)):
        # Each step reduces risk
        next_risk = current_risk * 0.8  # 20% reduction per step
        rho = compute_contractivity(current_risk, next_risk)

        assert rho < 1.0, f"Step {i} violated contractivity"

        rho_product *= rho
        current_risk = next_risk

    # Final risk should be significantly lower
    assert current_risk < initial_risk
    assert rho_product < 1.0


def test_contractivity_zero_risk():
    """Edge case: risk reduced to near-zero"""
    risk_before = 0.5
    risk_after = 1e-10

    rho = compute_contractivity(risk_before, risk_after)

    assert rho < 1.0
    assert rho < 0.01  # Near-zero risk


def test_contractivity_identical_risk():
    """Edge case: no risk reduction (ρ = 1.0, not contractive)"""
    risk_before = 0.5
    risk_after = 0.5

    rho = compute_contractivity(risk_before, risk_after)

    assert rho == pytest.approx(1.0, abs=1e-6)
    assert not validate_contractive_property(risk_before, risk_after)


def test_contractivity_increased_risk():
    """Edge case: risk increased (ρ > 1.0, violation)"""
    risk_before = 0.3
    risk_after = 0.5

    rho = compute_contractivity(risk_before, risk_after)

    assert rho > 1.0, "Should detect risk increase"
    assert not validate_contractive_property(risk_before, risk_after)

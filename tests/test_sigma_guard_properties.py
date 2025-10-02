"""
Property-based tests for Σ-Guard using hypothesis.

These tests validate the robustness of the Σ-Guard fail-closed security gate
by generating a wide range of inputs (dictionaries, numbers, strings) and ensuring
that it always behaves as expected, especially maintaining fail-closed design.

References:
- Issue: Testing: Validar o Σ-Guard com Testes de Propriedade
- Implementation: penin/guard/sigma_guard_complete.py
"""

import math

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from penin.guard.sigma_guard_complete import (
    GateMetrics,
    GateResult,
    GateStatus,
    SigmaGuard,
    SigmaGuardVerdict,
)

# ============================================================================
# Strategy Definitions
# ============================================================================


def valid_floats(min_value: float = 0.0, max_value: float = 2.0) -> st.SearchStrategy[float]:
    """Generate valid float values within range, excluding NaN and infinity."""
    return st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_infinity=False,
    )


@st.composite
def valid_gate_metrics(draw) -> GateMetrics:
    """Generate valid GateMetrics for testing."""
    return GateMetrics(
        rho=draw(valid_floats(0.0, 1.5)),
        ece=draw(valid_floats(0.0, 0.1)),
        rho_bias=draw(valid_floats(0.5, 1.5)),
        sr_score=draw(valid_floats(0.0, 1.0)),
        omega_g=draw(valid_floats(0.0, 1.0)),
        delta_linf=draw(valid_floats(0.0, 0.2)),
        caos_plus=draw(valid_floats(0.0, 50.0)),
        cost_increase=draw(valid_floats(0.0, 0.5)),
        kappa=draw(valid_floats(0.0, 50.0)),
        consent=draw(st.booleans()),
        eco_ok=draw(st.booleans()),
    )


@st.composite
def passing_gate_metrics(draw) -> GateMetrics:
    """Generate GateMetrics that should pass all gates."""
    return GateMetrics(
        rho=draw(valid_floats(0.0, 0.98)),  # < 0.99
        ece=draw(valid_floats(0.0, 0.009)),  # <= 0.01
        rho_bias=draw(valid_floats(0.5, 1.04)),  # <= 1.05
        sr_score=draw(valid_floats(0.81, 1.0)),  # >= 0.80
        omega_g=draw(valid_floats(0.86, 1.0)),  # >= 0.85
        delta_linf=draw(valid_floats(0.011, 0.2)),  # >= 0.01
        caos_plus=draw(valid_floats(0.0, 50.0)),  # Not validated in current implementation; does not affect test results
        cost_increase=draw(valid_floats(0.0, 0.09)),  # <= 0.10
        kappa=draw(valid_floats(21.0, 50.0)),  # >= 20.0
        consent=True,
        eco_ok=True,
    )


@st.composite
def failing_gate_metrics(draw) -> tuple[GateMetrics, str]:
    """Generate GateMetrics that should fail at least one gate, with reason."""
    # Choose which gate to violate
    gate_to_fail = draw(st.sampled_from([
        "rho", "ece", "rho_bias", "sr_score", "omega_g",
        "delta_linf", "cost_increase", "kappa", "consent", "eco_ok"
    ]))

    # Start with passing values
    metrics = GateMetrics(
        rho=draw(valid_floats(0.0, 0.98)),
        ece=draw(valid_floats(0.0, 0.009)),
        rho_bias=draw(valid_floats(0.5, 1.04)),
        sr_score=draw(valid_floats(0.81, 1.0)),
        omega_g=draw(valid_floats(0.86, 1.0)),
        delta_linf=draw(valid_floats(0.011, 0.2)),
        caos_plus=draw(valid_floats(0.0, 50.0)),
        cost_increase=draw(valid_floats(0.0, 0.09)),
        kappa=draw(valid_floats(21.0, 50.0)),
        consent=True,
        eco_ok=True,
    )

    # Violate the chosen gate
    if gate_to_fail == "rho":
        metrics.rho = draw(valid_floats(1.0, 1.5))
    elif gate_to_fail == "ece":
        metrics.ece = draw(valid_floats(0.011, 0.1))
    elif gate_to_fail == "rho_bias":
        metrics.rho_bias = draw(valid_floats(1.06, 1.5))
    elif gate_to_fail == "sr_score":
        metrics.sr_score = draw(valid_floats(0.0, 0.79))
    elif gate_to_fail == "omega_g":
        metrics.omega_g = draw(valid_floats(0.0, 0.84))
    elif gate_to_fail == "delta_linf":
        metrics.delta_linf = draw(valid_floats(0.0, 0.009))
    elif gate_to_fail == "cost_increase":
        metrics.cost_increase = draw(valid_floats(0.11, 0.5))
    elif gate_to_fail == "kappa":
        metrics.kappa = draw(valid_floats(0.0, 19.9))
    elif gate_to_fail == "consent":
        metrics.consent = False
    elif gate_to_fail == "eco_ok":
        metrics.eco_ok = False

    return metrics, gate_to_fail


# ============================================================================
# Property Tests: Fail-Closed Behavior
# ============================================================================


class TestFailClosedProperties:
    """Test fail-closed behavior with property-based testing."""

    @given(metrics=valid_gate_metrics())
    @settings(max_examples=200, deadline=None)
    def test_verdict_structure_is_always_valid(self, metrics: GateMetrics):
        """Property: Verdict structure is always valid regardless of input."""
        guard = SigmaGuard()
        verdict = guard.validate(metrics)

        # Verdict must have required fields
        assert isinstance(verdict, SigmaGuardVerdict)
        assert isinstance(verdict.passed, bool)
        assert isinstance(verdict.verdict, GateStatus)
        assert isinstance(verdict.action, str)
        assert isinstance(verdict.reason, str)
        assert isinstance(verdict.gates, list)
        assert len(verdict.gates) == 10  # All 10 gates
        assert isinstance(verdict.aggregate_score, float)
        assert verdict.aggregate_score >= 0.0
        assert len(verdict.hash_proof) == 64  # SHA-256 hex

    @given(metrics=valid_gate_metrics())
    @settings(max_examples=200, deadline=None)
    def test_fail_closed_never_promotes_on_violation(self, metrics: GateMetrics):
        """Property: System NEVER promotes when any gate fails (fail-closed)."""
        guard = SigmaGuard()
        verdict = guard.validate(metrics)

        # If any gate fails, must not promote
        any_gate_failed = any(not g.passed for g in verdict.gates)
        if any_gate_failed:
            assert verdict.passed is False
            assert verdict.verdict == GateStatus.FAIL
            assert verdict.action == "rollback"
            # Note: aggregate_score may be non-zero if some gates passed,
            # but the overall verdict is still FAIL (non-compensatory)
            assert verdict.aggregate_score >= 0.0

    @given(data=failing_gate_metrics())
    @settings(max_examples=200, deadline=None)
    def test_single_failure_causes_rollback(self, data: tuple[GateMetrics, str]):
        """Property: Single gate failure causes complete rollback (non-compensatory)."""
        metrics, expected_failure = data
        guard = SigmaGuard()
        verdict = guard.validate(metrics)

        # Must fail
        assert verdict.passed is False
        assert verdict.verdict == GateStatus.FAIL
        assert verdict.action == "rollback"

        # At least one gate must have failed
        failed_gates = [g for g in verdict.gates if not g.passed]
        assert len(failed_gates) >= 1

    @given(metrics=passing_gate_metrics())
    @settings(max_examples=100, deadline=None)
    def test_all_passing_gates_promotes(self, metrics: GateMetrics):
        """Property: When all gates pass, system promotes."""
        guard = SigmaGuard()
        verdict = guard.validate(metrics)

        # All gates should pass
        assert verdict.passed is True
        assert verdict.verdict == GateStatus.PASS
        assert verdict.action == "promote"
        assert all(g.passed for g in verdict.gates)
        assert verdict.aggregate_score > 0.0

    @given(
        rho=valid_floats(1.0, 1.5),  # Violates contractivity
        ece=valid_floats(0.0, 0.009),
        rho_bias=valid_floats(0.5, 1.04),
        sr_score=valid_floats(0.81, 1.0),
        omega_g=valid_floats(0.86, 1.0),
        delta_linf=valid_floats(0.011, 0.2),
        cost_increase=valid_floats(0.0, 0.09),
        kappa=valid_floats(21.0, 50.0),
    )
    @settings(max_examples=100, deadline=None)
    def test_contractivity_violation_always_fails(
        self, rho, ece, rho_bias, sr_score, omega_g, delta_linf, cost_increase, kappa
    ):
        """Property: Contractivity violation (ρ >= 1.0) always causes failure."""
        assume(rho >= 0.99)  # Ensure violation

        guard = SigmaGuard()
        metrics = GateMetrics(
            rho=rho, ece=ece, rho_bias=rho_bias, sr_score=sr_score,
            omega_g=omega_g, delta_linf=delta_linf, caos_plus=25.0,
            cost_increase=cost_increase, kappa=kappa, consent=True, eco_ok=True,
        )
        verdict = guard.validate(metrics)

        assert verdict.passed is False
        assert verdict.action == "rollback"


# ============================================================================
# Property Tests: Non-Compensatory Behavior
# ============================================================================


class TestNonCompensatoryProperties:
    """Test that excellent metrics cannot compensate for failures."""

    @given(
        failing_gate=st.sampled_from([
            "rho", "ece", "rho_bias", "sr_score", "omega_g",
            "delta_linf", "cost_increase", "kappa", "consent", "eco_ok"
        ])
    )
    @settings(max_examples=100, deadline=None)
    def test_excellent_metrics_cannot_compensate(self, failing_gate: str):
        """Property: Excellent metrics on other gates cannot compensate for one failure."""
        # Create excellent metrics
        metrics = GateMetrics(
            rho=0.5,  # Excellent
            ece=0.001,  # Excellent
            rho_bias=1.0,  # Perfect
            sr_score=0.99,  # Excellent
            omega_g=0.99,  # Excellent
            delta_linf=0.1,  # Excellent
            caos_plus=30.0,  # Excellent
            cost_increase=0.01,  # Excellent
            kappa=40.0,  # Excellent
            consent=True,
            eco_ok=True,
        )

        # Break one gate
        if failing_gate == "rho":
            metrics.rho = 1.2
        elif failing_gate == "ece":
            metrics.ece = 0.05
        elif failing_gate == "rho_bias":
            metrics.rho_bias = 1.15
        elif failing_gate == "sr_score":
            metrics.sr_score = 0.5
        elif failing_gate == "omega_g":
            metrics.omega_g = 0.5
        elif failing_gate == "delta_linf":
            metrics.delta_linf = 0.005
        elif failing_gate == "cost_increase":
            metrics.cost_increase = 0.3
        elif failing_gate == "kappa":
            metrics.kappa = 10.0
        elif failing_gate == "consent":
            metrics.consent = False
        elif failing_gate == "eco_ok":
            metrics.eco_ok = False

        guard = SigmaGuard()
        verdict = guard.validate(metrics)

        # Must still fail despite excellent other metrics
        assert verdict.passed is False
        assert verdict.verdict == GateStatus.FAIL
        assert verdict.action == "rollback"


# ============================================================================
# Property Tests: Boundary Conditions
# ============================================================================


class TestBoundaryProperties:
    """Test boundary conditions for all thresholds."""

    @given(epsilon=valid_floats(0.001, 0.01))
    @settings(max_examples=50, deadline=None)
    def test_rho_boundary_at_0_99(self, epsilon: float):
        """Property: ρ just below threshold passes, just above fails."""
        guard = SigmaGuard(rho_max=0.99)

        # Just below threshold - should pass
        metrics_pass = GateMetrics(
            rho=0.99 - epsilon,
            ece=0.005, rho_bias=1.02, sr_score=0.85, omega_g=0.90,
            delta_linf=0.02, caos_plus=25.0, cost_increase=0.05,
            kappa=25.0, consent=True, eco_ok=True,
        )
        verdict_pass = guard.validate(metrics_pass)
        rho_gate_pass = next(g for g in verdict_pass.gates if g.gate_name == "contractividade")
        assert rho_gate_pass.passed is True

        # Just above threshold - should fail
        metrics_fail = GateMetrics(
            rho=0.99 + epsilon,
            ece=0.005, rho_bias=1.02, sr_score=0.85, omega_g=0.90,
            delta_linf=0.02, caos_plus=25.0, cost_increase=0.05,
            kappa=25.0, consent=True, eco_ok=True,
        )
        verdict_fail = guard.validate(metrics_fail)
        rho_gate_fail = next(g for g in verdict_fail.gates if g.gate_name == "contractividade")
        assert rho_gate_fail.passed is False

    @given(epsilon=valid_floats(0.0001, 0.005))
    @settings(max_examples=50, deadline=None)
    def test_ece_boundary_at_0_01(self, epsilon: float):
        """Property: ECE at boundary behaves correctly."""
        guard = SigmaGuard(ece_max=0.01)

        # Just below threshold - should pass
        metrics_pass = GateMetrics(
            rho=0.95,
            ece=0.01 - epsilon,
            rho_bias=1.02, sr_score=0.85, omega_g=0.90,
            delta_linf=0.02, caos_plus=25.0, cost_increase=0.05,
            kappa=25.0, consent=True, eco_ok=True,
        )
        verdict_pass = guard.validate(metrics_pass)
        ece_gate_pass = next(g for g in verdict_pass.gates if g.gate_name == "calibration")
        assert ece_gate_pass.passed is True

        # Just above threshold - should fail
        metrics_fail = GateMetrics(
            rho=0.95,
            ece=0.01 + epsilon,
            rho_bias=1.02, sr_score=0.85, omega_g=0.90,
            delta_linf=0.02, caos_plus=25.0, cost_increase=0.05,
            kappa=25.0, consent=True, eco_ok=True,
        )
        verdict_fail = guard.validate(metrics_fail)
        ece_gate_fail = next(g for g in verdict_fail.gates if g.gate_name == "calibration")
        assert ece_gate_fail.passed is False


# ============================================================================
# Property Tests: Extreme Values & Error Handling
# ============================================================================


class TestExtremeValueProperties:
    """Test handling of extreme values."""

    def test_zero_values_handled_correctly(self):
        """Property: Zero values are handled without errors."""
        guard = SigmaGuard()
        metrics = GateMetrics(
            rho=0.0,
            ece=0.0,
            rho_bias=0.0,  # Will fail bias gate
            sr_score=0.0,  # Will fail SR gate
            omega_g=0.0,  # Will fail coherence gate
            delta_linf=0.0,  # Will fail improvement gate
            caos_plus=0.0,
            cost_increase=0.0,
            kappa=0.0,  # Will fail kappa gate
            consent=True,
            eco_ok=True,
        )

        # Should not raise error
        verdict = guard.validate(metrics)
        assert isinstance(verdict, SigmaGuardVerdict)
        assert verdict.passed is False  # Multiple failures

    def test_maximum_values_handled_correctly(self):
        """Property: Maximum values are handled without errors."""
        guard = SigmaGuard()
        metrics = GateMetrics(
            rho=1.5,  # Will fail
            ece=0.1,  # Will fail
            rho_bias=1.5,  # Will fail
            sr_score=1.0,  # Max, should pass
            omega_g=1.0,  # Max, should pass
            delta_linf=0.2,  # High, should pass
            caos_plus=50.0,  # High value
            cost_increase=0.5,  # Will fail
            kappa=50.0,  # High, should pass
            consent=True,
            eco_ok=True,
        )

        # Should not raise error
        verdict = guard.validate(metrics)
        assert isinstance(verdict, SigmaGuardVerdict)
        assert verdict.passed is False  # Multiple failures

    def test_nan_and_infinity_handled_safely(self):
        """Property: NaN and infinity values don't crash the system."""
        guard = SigmaGuard()

        # Test with NaN values
        test_cases = [
            # NaN in rho
            GateMetrics(
                rho=math.nan, ece=0.005, rho_bias=1.0, sr_score=0.85, omega_g=0.90,
                delta_linf=0.02, caos_plus=25.0, cost_increase=0.05,
                kappa=25.0, consent=True, eco_ok=True,
            ),
            # Infinity in ece
            GateMetrics(
                rho=0.95, ece=math.inf, rho_bias=1.0, sr_score=0.85, omega_g=0.90,
                delta_linf=0.02, caos_plus=25.0, cost_increase=0.05,
                kappa=25.0, consent=True, eco_ok=True,
            ),
            # Negative infinity in kappa
            GateMetrics(
                rho=0.95, ece=0.005, rho_bias=1.0, sr_score=0.85, omega_g=0.90,
                delta_linf=0.02, caos_plus=25.0, cost_increase=0.05,
                kappa=-math.inf, consent=True, eco_ok=True,
            ),
        ]

        for metrics in test_cases:
            # Should handle gracefully (may fail gates, but shouldn't crash)
            try:
                verdict = guard.validate(metrics)
                # If it doesn't crash, verify it returns a verdict
                assert isinstance(verdict, SigmaGuardVerdict)
                # With invalid inputs, should not promote
                # (NaN comparisons are False, so gates should fail)
            except (ValueError, TypeError):
                # Acceptable to raise these errors for invalid inputs
                pass


# ============================================================================
# Property Tests: Idempotency & Determinism
# ============================================================================


class TestIdempotencyProperties:
    """Test idempotency and determinism."""

    @given(metrics=valid_gate_metrics())
    @settings(max_examples=100, deadline=None)
    def test_validation_is_deterministic(self, metrics: GateMetrics):
        """Property: Same metrics always produce same verdict."""
        guard = SigmaGuard()

        verdict1 = guard.validate(metrics)
        verdict2 = guard.validate(metrics)

        # Same inputs produce same outputs
        assert verdict1.passed == verdict2.passed
        assert verdict1.verdict == verdict2.verdict
        assert verdict1.action == verdict2.action
        assert len(verdict1.gates) == len(verdict2.gates)

        # Each gate result should be identical
        for g1, g2 in zip(verdict1.gates, verdict2.gates, strict=True):
            assert g1.gate_name == g2.gate_name
            assert g1.passed == g2.passed
            assert g1.status == g2.status
            assert g1.value == g2.value
            assert g1.threshold == g2.threshold

    @given(metrics=valid_gate_metrics())
    @settings(max_examples=50, deadline=None)
    def test_multiple_guards_behave_identically(self, metrics: GateMetrics):
        """Property: Multiple guard instances with same config behave identically."""
        guard1 = SigmaGuard()
        guard2 = SigmaGuard()

        verdict1 = guard1.validate(metrics)
        verdict2 = guard2.validate(metrics)

        assert verdict1.passed == verdict2.passed
        assert verdict1.verdict == verdict2.verdict
        assert verdict1.action == verdict2.action


# ============================================================================
# Property Tests: Gate Independence
# ============================================================================


class TestGateIndependenceProperties:
    """Test that gates are evaluated independently."""

    @given(metrics=valid_gate_metrics())
    @settings(max_examples=100, deadline=None)
    def test_all_gates_always_evaluated(self, metrics: GateMetrics):
        """Property: All 10 gates are always evaluated regardless of early failures."""
        guard = SigmaGuard()
        verdict = guard.validate(metrics)

        # All 10 gates must be present
        assert len(verdict.gates) == 10

        # Expected gate names
        expected_gates = {
            "contractividade", "calibration", "bias", "self_reflection",
            "global_coherence", "improvement", "cost_control", "kappa",
            "consent", "ecological"
        }
        actual_gates = {g.gate_name for g in verdict.gates}
        assert expected_gates == actual_gates

    @given(metrics=valid_gate_metrics())
    @settings(max_examples=100, deadline=None)
    def test_each_gate_has_valid_result(self, metrics: GateMetrics):
        """Property: Each gate result is properly structured."""
        guard = SigmaGuard()
        verdict = guard.validate(metrics)

        for gate in verdict.gates:
            assert isinstance(gate, GateResult)
            assert isinstance(gate.gate_name, str)
            assert len(gate.gate_name) > 0
            assert isinstance(gate.status, GateStatus)
            assert isinstance(gate.value, float)
            assert isinstance(gate.threshold, float)
            assert isinstance(gate.passed, bool)
            assert isinstance(gate.reason, str)
            assert len(gate.reason) > 0
            assert isinstance(gate.timestamp, str)
            assert len(gate.timestamp) > 0


# ============================================================================
# Run tests
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

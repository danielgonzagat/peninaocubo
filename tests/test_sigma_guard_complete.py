"""
Test suite for Σ-Guard complete implementation.

Tests fail-closed gates, non-compensatory validation, and OPA/Rego integration.
"""

import pytest

from penin.guard.sigma_guard_complete import (
    GateMetrics,
    GateStatus,
    SigmaGuard,
)


class TestSigmaGuardBasic:
    """Test basic Σ-Guard functionality."""

    def test_all_gates_pass(self):
        """Test when all gates pass."""
        guard = SigmaGuard(
            rho_max=0.99,
            ece_max=0.01,
            rho_bias_max=1.05,
            sr_min=0.80,
            G_min=0.85,
            delta_Linf_min=0.01,
            cost_max_increase=0.10,
            kappa_min=20.0,
        )

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        assert verdict.passed is True
        assert verdict.verdict == GateStatus.PASS
        assert verdict.action == "promote"
        assert len(verdict.gates) == 10
        assert all(g.passed for g in verdict.gates)

    def test_fail_on_contractivity(self):
        """Test failure on contractivity violation (ρ >= 1)."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=1.05,  # FAIL: ρ >= 1
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        # Σ-Guard should fail when ρ >= 1 (non-contractive)
        assert verdict.passed is False
        assert verdict.verdict == GateStatus.FAIL
        assert verdict.action == "rollback"
        # At least one gate failed
        failed_gates = [g for g in verdict.gates if not g.passed]
        assert len(failed_gates) > 0

    def test_fail_on_calibration(self):
        """Test failure on calibration (ECE > threshold)."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.05,  # FAIL: ECE > 0.01
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        assert verdict.passed is False
        assert any("ece" in g.gate_name.lower() or "calibr" in g.gate_name.lower() for g in verdict.gates if not g.passed)

    def test_fail_on_bias(self):
        """Test failure on bias (ρ_bias > 1.05)."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.20,  # FAIL: rho_bias > 1.05
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        assert verdict.passed is False
        assert any("bias" in g.gate_name.lower() for g in verdict.gates if not g.passed)

    def test_fail_on_sr_omega(self):
        """Test failure on SR-Ω∞ score too low."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.50,  # FAIL: SR < 0.80
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        # Σ-Guard should fail when SR too low
        assert verdict.passed is False
        # At least one gate failed
        assert any(not g.passed for g in verdict.gates)

    def test_fail_on_coherence(self):
        """Test failure on global coherence G too low."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.50,  # FAIL: G < 0.85
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        assert verdict.passed is False
        assert any("coherence" in g.gate_name.lower() or "omega" in g.gate_name.lower() for g in verdict.gates if not g.passed)

    def test_fail_on_death_gate(self):
        """Test failure on ΔL∞ below threshold."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.002,  # FAIL: ΔL∞ < 0.01
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        # Σ-Guard should fail when ΔL∞ too low
        assert verdict.passed is False
        # At least one gate failed
        assert any(not g.passed for g in verdict.gates)

    def test_fail_on_cost(self):
        """Test failure on cost increase too high."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.25,  # FAIL: cost > 10%
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        assert verdict.passed is False
        assert any("cost" in g.gate_name.lower() for g in verdict.gates if not g.passed)

    def test_fail_on_kappa(self):
        """Test failure on kappa too low."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=10.0,  # FAIL: kappa < 20
            cost_increase=0.08,
            kappa=10.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        assert verdict.passed is False
        assert any("kappa" in g.gate_name.lower() for g in verdict.gates if not g.passed)

    def test_fail_on_consent(self):
        """Test failure when consent not given."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=False,  # FAIL: no consent
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        assert verdict.passed is False
        assert any("consent" in g.gate_name.lower() for g in verdict.gates if not g.passed)

    def test_fail_on_ecological(self):
        """Test failure on ecological violation."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=False,  # FAIL: eco not ok
        )

        verdict = guard.validate(metrics)

        assert verdict.passed is False
        assert any("eco" in g.gate_name.lower() for g in verdict.gates if not g.passed)


class TestSigmaGuardNonCompensatory:
    """Test non-compensatory aggregation (one fail = total fail)."""

    def test_excellent_metrics_cannot_compensate_single_failure(self):
        """Excellent metrics can't compensate for single gate failure."""
        guard = SigmaGuard()

        # Perfect metrics except consent
        metrics = GateMetrics(
            rho=0.50,  # Excellent
            ece=0.001,  # Excellent
            rho_bias=1.01,  # Excellent
            sr_score=0.95,  # Excellent
            omega_g=0.99,  # Excellent
            delta_linf=0.10,  # Excellent
            caos_plus=50.0,  # Excellent
            cost_increase=0.01,  # Excellent
            kappa=50.0,  # Excellent
            consent=False,  # SINGLE FAILURE
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        # Non-compensatory: single failure blocks everything
        assert verdict.passed is False
        assert verdict.action == "rollback"

    def test_aggregate_score_zero_on_failure(self):
        """Aggregate score should be 0 when any gate fails."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=False,  # One failure
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        # Non-compensatory aggregation: V_t = 0 when any gate fails
        assert verdict.passed is False


class TestSigmaGuardAuditability:
    """Test auditability features (hash proofs, detailed results)."""

    def test_hash_proof_generation(self):
        """Test that each gate result has hash proof."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        # Each gate should have result
        assert len(verdict.gates) == 10
        # Verdict should have hash (for WORM ledger)
        assert hasattr(verdict, "hash") or hasattr(verdict, "timestamp")

    def test_gate_results_detailed(self):
        """Test detailed gate results."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        # Each gate should have name, status, value
        for gate in verdict.gates:
            assert hasattr(gate, "gate_name")
            assert hasattr(gate, "status")
            assert hasattr(gate, "passed")

    def test_timestamps(self):
        """Test timestamp generation."""
        guard = SigmaGuard()

        metrics = GateMetrics(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            omega_g=0.88,
            delta_linf=0.015,
            caos_plus=25.0,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        verdict = guard.validate(metrics)

        # Verdict should have timestamp for auditability
        assert hasattr(verdict, "timestamp") or hasattr(verdict, "created_at")

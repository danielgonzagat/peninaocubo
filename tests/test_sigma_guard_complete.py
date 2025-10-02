"""
Test suite for Σ-Guard complete implementation.

Tests fail-closed gates, non-compensatory validation, and OPA/Rego integration.
"""

import pytest

from penin.guard.sigma_guard_complete import (
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

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.passed is True
        assert verdict.verdict == GateStatus.PASS
        assert verdict.action == "promote"
        assert len(verdict.gates) == 10
        assert all(g.passed for g in verdict.gates)

    def test_fail_on_contractivity(self):
        """Test failure on contractivity violation (ρ ≥ 1)."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=1.05,  # FAIL: ρ ≥ 1
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.passed is False
        assert verdict.verdict == GateStatus.FAIL
        assert verdict.action == "rollback"
        assert "contractivity" in verdict.reason.lower()

    def test_fail_on_calibration(self):
        """Test failure on calibration (ECE too high)."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=0.85,
            ece=0.025,  # FAIL: ECE > 0.01
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.passed is False
        assert "calibration" in verdict.reason.lower()

    def test_fail_on_bias(self):
        """Test failure on bias violation."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.10,  # FAIL: ρ_bias > 1.05
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.passed is False
        assert "bias" in verdict.reason.lower()

    def test_fail_on_sr_omega(self):
        """Test failure on SR-Ω∞ too low."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.65,  # FAIL: SR < 0.80
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.passed is False
        assert "reflexivity" in verdict.reason.lower()

    def test_fail_on_coherence(self):
        """Test failure on global coherence too low."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.75,  # FAIL: G < 0.85
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.passed is False
        assert "coherence" in verdict.reason.lower()

    def test_fail_on_death_gate(self):
        """Test failure on Death gate (ΔL∞ < β_min)."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.005,  # FAIL: ΔL∞ < 0.01 → DEATH
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.passed is False
        assert "improvement" in verdict.reason.lower()

    def test_fail_on_cost(self):
        """Test failure on cost increase too high."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.15,  # FAIL: cost > 0.10
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.passed is False
        assert "cost" in verdict.reason.lower()

    def test_fail_on_kappa(self):
        """Test failure on kappa too low."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=15.0,  # FAIL: κ < 20.0
            consent=True,
            eco_ok=True,
        )

        assert verdict.passed is False
        assert "kappa" in verdict.reason.lower()

    def test_fail_on_consent(self):
        """Test failure on missing consent."""
        guard = SigmaGuard(consent_required=True)

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=False,  # FAIL: consent denied
            eco_ok=True,
        )

        assert verdict.passed is False
        assert "consent" in verdict.reason.lower()

    def test_fail_on_ecological(self):
        """Test failure on ecological constraints."""
        guard = SigmaGuard(eco_ok_required=True)

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=False,  # FAIL: eco not OK
        )

        assert verdict.passed is False
        assert "ecological" in verdict.reason.lower()


class TestSigmaGuardNonCompensatory:
    """Test non-compensatory behavior."""

    def test_excellent_metrics_cannot_compensate_single_failure(self):
        """Test that excellent metrics in other gates cannot compensate for one failure."""
        guard = SigmaGuard()

        # All gates excellent EXCEPT contractivity
        verdict = guard.validate(
            rho=1.05,  # FAIL
            ece=0.001,  # Excellent
            rho_bias=1.00,  # Excellent
            sr_score=0.95,  # Excellent
            G_coherence=0.95,  # Excellent
            delta_Linf=0.05,  # Excellent
            cost_increase=0.01,  # Excellent
            kappa=30.0,  # Excellent
            consent=True,
            eco_ok=True,
        )

        # Should still FAIL due to single gate failure
        assert verdict.passed is False
        assert verdict.action == "rollback"

    def test_aggregate_score_zero_on_failure(self):
        """Test that aggregate score is 0 when any gate fails."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=1.05,  # FAIL
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.aggregate_score == 0.0


class TestSigmaGuardAuditability:
    """Test auditability features."""

    def test_hash_proof_generation(self):
        """Test that verdict generates hash proof."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.hash_proof
        assert len(verdict.hash_proof) == 64  # SHA-256 hex

    def test_gate_results_detailed(self):
        """Test that all gate results are detailed."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert len(verdict.gates) == 10

        for gate in verdict.gates:
            assert gate.gate_name
            assert gate.status in [GateStatus.PASS, GateStatus.FAIL]
            assert gate.reason
            assert gate.timestamp

    def test_timestamps(self):
        """Test that timestamps are generated."""
        guard = SigmaGuard()

        verdict = guard.validate(
            rho=0.85,
            ece=0.005,
            rho_bias=1.02,
            sr_score=0.84,
            G_coherence=0.88,
            delta_Linf=0.015,
            cost_increase=0.08,
            kappa=25.0,
            consent=True,
            eco_ok=True,
        )

        assert verdict.timestamp
        for gate in verdict.gates:
            assert gate.timestamp


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

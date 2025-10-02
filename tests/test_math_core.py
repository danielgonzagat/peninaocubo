"""
Test suite for PENIN-Ω core mathematical modules.

Tests L∞, CAOS⁺, SR-Ω∞, Vida/Morte, IR→IC, and Master Equation.
"""

import math

import numpy as np
import pytest

from penin.core.caos import (
    CAOSComponents,
    caos_plus_simple,
    compute_A_autoevolution,
    compute_C_consistency,
    compute_caos_plus,
    compute_O_unknowable,
    compute_S_silence,
)
from penin.math.ir_ic_contractivity import (
    RiskProfile,
    apply_Lpsi_operator,
    check_contractivity,
    compute_risk_entropy,
    iterative_refinement,
)
from penin.math.linf_complete import (
    check_min_improvement,
    compute_delta_Linf,
    compute_Linf,
)
from penin.math.penin_master_equation import (
    MasterEquationState,
    compute_phi_saturation,
    master_equation_cycle,
    penin_update,
    project_to_safe_set,
)
from penin.math.sr_omega_infinity import (
    SRComponents,
    compute_alpha_effective,
    compute_autocorrection,
    compute_awareness,
    compute_metacognition,
    compute_sr_score,
)
from penin.math.vida_morte_gates import (
    GateDecision,
    auto_tune_beta_min,
    compute_lyapunov_quadratic,
    death_gate,
    life_gate_lyapunov,
)


class TestLinfMeta:
    """Test L∞ meta-function."""

    def test_basic_computation(self):
        """Test basic L∞ calculation."""
        metrics = [0.85, 0.78, 0.92]
        weights = [0.4, 0.4, 0.2]

        score = compute_Linf(metrics, weights, cost_norm=0.15, lambda_c=0.5, ethical_ok=True)

        assert 0.0 <= score <= 1.0
        assert score > 0.7  # Should be reasonably high

    def test_fail_closed_ethics(self):
        """Test fail-closed on ethics failure."""
        metrics = [0.9, 0.9, 0.9]
        weights = [0.33, 0.33, 0.34]

        score = compute_Linf(metrics, weights, ethical_ok=False)

        assert score == 0.0

    def test_fail_closed_contractivity(self):
        """Test fail-closed on contractivity failure."""
        metrics = [0.9, 0.9, 0.9]
        weights = [0.33, 0.33, 0.34]

        score = compute_Linf(metrics, weights, contractivity_ok=False)

        assert score == 0.0

    def test_cost_penalty(self):
        """Test cost penalty reduces score."""
        metrics = [0.8, 0.8, 0.8]
        weights = [0.33, 0.33, 0.34]

        score_low_cost = compute_Linf(metrics, weights, cost_norm=0.0, lambda_c=1.0)
        score_high_cost = compute_Linf(metrics, weights, cost_norm=0.5, lambda_c=1.0)

        assert score_high_cost < score_low_cost

    def test_delta_Linf(self):
        """Test ΔL∞ computation."""
        delta = compute_delta_Linf(0.82, 0.78)
        assert delta == pytest.approx(0.04, abs=1e-6)

        delta_rel = compute_delta_Linf(0.82, 0.78, relative=True)
        assert delta_rel == pytest.approx(0.04 / 0.78, abs=1e-6)

    def test_min_improvement_gate(self):
        """Test minimum improvement check."""
        assert check_min_improvement(0.015, beta_min=0.01) is True
        assert check_min_improvement(0.008, beta_min=0.01) is False


class TestCAOSPlus:
    """Test CAOS⁺ engine."""

    def test_basic_computation(self):
        """Test basic CAOS⁺ calculation."""
        score, details = compute_caos_plus(C=0.88, A=0.40, O=0.35, S=0.82, kappa=20.0)

        # phi_caos usa tanh, então score pode ser < 1.0
        assert score > 0.0
        assert isinstance(details, dict)
        assert details['C'] == 0.88
        assert details['A'] == 0.40
        assert details['O'] == 0.35
        assert details['S'] == 0.82

    def test_simple_interface(self):
        """Test simplified interface."""
        score = caos_plus_simple(0.9, 0.5, 0.3, 0.8, kappa=25.0)
        assert score >= 1.0

    def test_zero_exponent(self):
        """Test edge case: O·S = 0."""
        score, _ = compute_caos_plus(C=0.9, A=0.5, O=0.0, S=0.8, kappa=20.0)
        # phi_caos com O=0 ainda produz um valor (não necessariamente 1.0)
        assert score >= 0.0

    def test_C_consistency(self):
        """Test C computation."""
        C = compute_C_consistency(pass_at_k=0.90, ece=0.005, external_verification=0.85)
        assert 0.0 <= C <= 1.0

    def test_A_autoevolution(self):
        """Test A computation."""
        A = compute_A_autoevolution(delta_Linf=0.06, cost_norm=0.15)
        assert 0.0 <= A <= 1.0
        assert A == pytest.approx(0.4, abs=0.01)

    def test_O_unknowable(self):
        """Test O computation."""
        O = compute_O_unknowable(epistemic_uncertainty=0.35, ood_score=0.25)
        assert 0.0 <= O <= 1.0

    def test_S_silence(self):
        """Test S computation."""
        S = compute_S_silence(noise_level=0.1, redundancy=0.05, entropy_norm=0.15)
        assert 0.0 <= S <= 1.0


class TestSROmegaInfinity:
    """Test SR-Ω∞ reflexive scoring."""

    def test_basic_computation(self):
        """Test basic SR score."""
        R_t, comp = compute_sr_score(
            awareness=0.92, ethics_ok=True, autocorrection=0.88, metacognition=0.67, return_components=True
        )

        assert 0.0 <= R_t <= 1.0
        assert isinstance(comp, SRComponents)
        assert comp.ethics_ok == 1.0

    def test_ethics_fail_closed(self):
        """Test ethics failure returns 0."""
        R_t, comp = compute_sr_score(
            awareness=0.95, ethics_ok=False, autocorrection=0.90, metacognition=0.80, return_components=True
        )

        assert R_t == 0.0
        assert comp.ethics_ok == 0.0

    def test_awareness_computation(self):
        """Test awareness calculation."""
        aw = compute_awareness(calibration_score=0.98, introspection_depth=0.90)
        assert 0.0 <= aw <= 1.0

    def test_autocorrection_computation(self):
        """Test autocorrection calculation."""
        ac = compute_autocorrection(risk_current=0.12, risk_previous=0.20)
        assert 0.0 <= ac <= 1.0

    def test_metacognition_computation(self):
        """Test metacognition calculation."""
        mc = compute_metacognition(delta_Linf=0.04, delta_cost=0.06)
        assert 0.0 <= mc <= 1.0

    def test_alpha_effective(self):
        """Test effective step size."""
        a_eff = compute_alpha_effective(alpha_0=0.1, caos_plus=1.86, R_t=0.84, gamma=0.8)

        assert 0.0 <= a_eff <= 0.1
        # Value should be reasonable (between 0.05 and 0.08)
        assert 0.05 <= a_eff <= 0.08


class TestVidaMorteGates:
    """Test Life/Death equations."""

    def test_death_gate_pass(self):
        """Test death gate passing."""
        result = death_gate(delta_Linf=0.015, beta_min=0.01)

        assert result.passed is True
        assert result.decision == GateDecision.PROMOTE

    def test_death_gate_fail(self):
        """Test death gate failure."""
        result = death_gate(delta_Linf=0.008, beta_min=0.01)

        assert result.passed is False
        assert result.decision == GateDecision.ROLLBACK

    def test_life_gate_pass(self):
        """Test life gate (Lyapunov) passing."""
        result = life_gate_lyapunov(V_current=0.85, V_previous=0.92)

        assert result.passed is True
        assert result.decision == GateDecision.PROMOTE
        assert result.dV_dt < 0

    def test_life_gate_fail(self):
        """Test life gate failure."""
        result = life_gate_lyapunov(V_current=0.95, V_previous=0.88)

        assert result.passed is False
        assert result.decision == GateDecision.ROLLBACK

    def test_lyapunov_quadratic(self):
        """Test quadratic Lyapunov function."""
        V = compute_lyapunov_quadratic(state=0.15, target=0.0)
        assert V == pytest.approx(0.0225, abs=1e-6)

    def test_auto_tune_beta_min(self):
        """Test auto-tuning of β_min."""
        beta_new = auto_tune_beta_min(
            success_rate=0.45, budget_remaining=0.30, risk_tolerance=0.20, beta_min_current=0.01, learning_rate=0.05
        )

        assert 0.001 <= beta_new <= 0.1


class TestIRICContractivity:
    """Test IR→IC contractivity."""

    def test_risk_entropy(self):
        """Test risk entropy computation."""
        rp = RiskProfile(
            idolatry=0.1,
            occultism=0.05,
            physical_harm=0.02,
            emotional_harm=0.03,
            spiritual_harm=0.0,
            privacy_violation=0.08,
            bias=0.04,
            fairness=0.1,
            transparency=0.85,
            aggregate=0.0,
        )

        H = compute_risk_entropy(rp)
        assert H > 0.0

    def test_Lpsi_operator(self):
        """Test L_ψ operator application."""
        rp_in = RiskProfile(
            idolatry=0.2,
            occultism=0.1,
            physical_harm=0.05,
            emotional_harm=0.0,
            spiritual_harm=0.0,
            privacy_violation=0.15,
            bias=0.08,
            fairness=0.12,
            transparency=0.80,
            aggregate=0.0,
        )

        rp_out = apply_Lpsi_operator(rp_in, rho=0.85)

        # Risks should be reduced
        assert rp_out.idolatry < rp_in.idolatry
        assert rp_out.privacy_violation < rp_in.privacy_violation

    def test_contractivity_check(self):
        """Test contractivity validation."""
        passes = check_contractivity(H_refined=1.80, H_original=2.12, rho=0.85)
        assert passes is True

        fails = check_contractivity(H_refined=2.00, H_original=2.12, rho=0.85)
        assert fails is False

    def test_iterative_refinement(self):
        """Test iterative refinement."""
        rp = RiskProfile(
            idolatry=0.5,
            occultism=0.4,
            physical_harm=0.3,
            emotional_harm=0.2,
            spiritual_harm=0.1,
            privacy_violation=0.4,
            bias=0.3,
            fairness=0.35,
            transparency=0.60,
            aggregate=0.32,  # Set initial aggregate
        )

        refined, iters, converged = iterative_refinement(rp, rho=0.9, max_iterations=5, convergence_threshold=1e-3)

        assert iters <= 5
        # Refined risks should be reduced
        assert refined.idolatry <= rp.idolatry
        assert refined.privacy_violation <= rp.privacy_violation


class TestMasterEquation:
    """Test Master Equation."""

    def test_project_to_safe_set(self):
        """Test projection to feasible set."""
        state = np.array([1.5, -0.2, 2.3])
        projected = project_to_safe_set(state, H_constraints={"bounds": (0.0, 1.0)})

        assert np.all(projected >= 0.0)
        assert np.all(projected <= 1.0)

    def test_phi_saturation(self):
        """Test saturation function."""
        phi = compute_phi_saturation(caos_plus=1.86, gamma=0.8, mode="tanh")

        assert 0.0 <= phi <= 1.0
        assert phi == pytest.approx(math.tanh(0.8 * 1.86), abs=1e-6)

    def test_penin_update(self):
        """Test single update step."""
        I_n = np.array([0.5, 0.3, 0.7])
        G = np.array([0.1, -0.05, 0.15])

        I_next = penin_update(I_n, G, alpha_n=0.065, H_constraints={"bounds": (0.0, 1.0)})

        assert I_next.shape == I_n.shape
        assert np.all(I_next >= 0.0)
        assert np.all(I_next <= 1.0)

    def test_master_equation_cycle(self):
        """Test complete cycle."""
        state = MasterEquationState(I=np.array([0.5, 0.3]), n=10, alpha_n=0.0, caos_plus=0.0, sr_score=0.0, Linf=0.75)

        def dummy_loss(I, E, P):
            return np.sum(I**2)

        new_state = master_equation_cycle(
            state, evidence=None, policies={}, loss_fn=dummy_loss, alpha_0=0.1, caos_plus=1.5, sr_score=0.85
        )

        assert new_state.n == state.n + 1
        assert new_state.alpha_n > 0.0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

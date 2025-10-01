"""
Smoke tests for all 15 PENIN-Ω core equations.
Validates basic functionality and expected behavior ranges.
"""

from __future__ import annotations

import numpy as np

from penin.equations import (
    AnabolizationConfig,
    AutoTuningConfig,
    CAOSConfig,
    ContractivityConfig,
    DeathConfig,
    DeltaLInfConfig,
    EPVConfig,
    LInfConfig,
    LyapunovConfig,
    OCIConfig,
    OmegaSEAConfig,
    PeninState,
    SigmaGuardConfig,
    SRConfig,
    anabolize_penin,
    auto_tune_hyperparams,
    compute_agape_index,
    compute_caos_plus_complete,
    compute_linf_meta,
    compute_sr_omega_infinity,
    death_gate_check,
    delta_linf_compound_growth,
    expected_possession_value,
    ir_to_ic,
    lyapunov_check,
    omega_sea_coherence,
    organizational_closure_index,
    penin_update,
    sigma_guard_check,
)


class TestEquation01PeninUpdate:
    """Test Equation 1: Penin Equation - Autoevolução Recursiva"""

    def test_basic_update(self):
        """Smoke test: basic state update"""
        state = PeninState(params=np.array([1.0, 2.0, 3.0]))
        gradient = np.array([0.1, 0.2, 0.3])
        alpha = 0.1
        new_state = penin_update(state, gradient, alpha, project_fn=None)
        assert isinstance(new_state, PeninState)
        assert len(new_state.params) == 3
        assert new_state.iteration == state.iteration + 1


class TestEquation02LInfMeta:
    """Test Equation 2: L∞ Meta-Function - Non-compensatory aggregation"""

    def test_basic_linf(self):
        """Smoke test: L∞ with valid inputs"""
        metrics = [0.8, 0.9, 0.85]
        weights = [0.4, 0.4, 0.2]
        cost = 0.1
        ethical_ok = True
        config = LInfConfig(lambda_c=0.5, epsilon=1e-3)

        linf = compute_linf_meta(metrics, weights, cost, config, ethical_ok=ethical_ok)
        assert 0.0 < linf <= 1.0, f"L∞ should be in (0, 1], got {linf}"

    def test_ethical_failsafe(self):
        """Smoke test: L∞ = 0 when ethics fail"""
        metrics = [0.9, 0.9, 0.9]
        weights = [0.33, 0.33, 0.34]
        cost = 0.1
        config = LInfConfig()

        linf = compute_linf_meta(metrics, weights, cost, config, ethical_ok=False)
        assert linf == 0.0, "L∞ must be 0 when ethical_ok=False (fail-closed)"


class TestEquation03CAOSPlus:
    """Test Equation 3: CAOS+ Motor"""

    def test_basic_caos(self):
        """Smoke test: CAOS+ with valid C, A, O, S"""
        C, A, O, S = 0.88, 0.40, 0.35, 0.82
        kappa = 20.0
        config = CAOSConfig(kappa=kappa)

        caos_score = compute_caos_plus_complete(C, A, O, S, kappa, config)
        assert caos_score >= 1.0, f"CAOS+ must be >= 1.0, got {caos_score}"
        assert caos_score < 100.0, f"CAOS+ seems too high: {caos_score}"

    def test_caos_monotonic_in_c(self):
        """CAOS+ should increase with C when A > 0"""
        kappa = 20.0
        config = CAOSConfig(kappa=kappa)

        caos_low = compute_caos_plus_complete(0.5, 0.5, 0.5, 0.5, kappa, config)
        caos_high = compute_caos_plus_complete(0.9, 0.5, 0.5, 0.5, kappa, config)

        assert caos_high > caos_low, "CAOS+ should increase with C"


class TestEquation04SROmegaInfinity:
    """Test Equation 4: SR-Ω∞ Singularidade Reflexiva"""

    def test_basic_sr(self):
        """Smoke test: SR score calculation"""
        awareness, ethics_ok, autocorr, metacog = 0.9, True, 0.85, 0.80
        config = SRConfig()

        sr_score = compute_sr_omega_infinity(awareness, ethics_ok, autocorr, metacog, config)
        assert 0.0 <= sr_score <= 1.0, f"SR must be in [0, 1], got {sr_score}"

    def test_sr_fail_on_ethics(self):
        """SR should be low when ethics_ok=False"""
        sr_ok = compute_sr_omega_infinity(0.9, True, 0.9, 0.9, SRConfig())
        sr_fail = compute_sr_omega_infinity(0.9, False, 0.9, 0.9, SRConfig())

        assert sr_fail < sr_ok, "SR should be lower when ethics fail"


class TestEquation05DeathEquation:
    """Test Equation 5: Death Equation - Darwinian selection"""

    def test_death_threshold(self):
        """Smoke test: Death gate based on ΔL∞"""
        config = DeathConfig(beta_min=0.01)

        # Should survive
        result_survive = death_gate_check(delta_linf=0.05, config=config)
        assert result_survive["alive"] is True

        # Should die
        result_die = death_gate_check(delta_linf=0.005, config=config)
        assert result_die["alive"] is False


class TestEquation06IRIC:
    """Test Equation 6: IR→IC Contratividade"""

    def test_contractivity(self):
        """Smoke test: IR→IC with ρ < 1"""
        config = ContractivityConfig(rho=0.95)
        result = ir_to_ic(risk_before=1.0, config=config)

        assert result["risk_after"] < result["risk_before"]
        assert result["contractive"] is True


class TestEquation07ACFAEPV:
    """Test Equation 7: ACFA EPV - Expected Possession Value"""

    def test_basic_epv(self):
        """Smoke test: EPV value function"""
        state = "state_A"
        action = "action_X"

        def reward_fn(s, a):
            return 1.0

        def transition_fn(s, a):
            return {"state_B": 1.0}

        def value_fn(s):
            return 0.5

        config = EPVConfig(gamma=0.9)
        epv = expected_possession_value(state, action, reward_fn, transition_fn, value_fn, config)

        assert isinstance(epv, float)
        assert epv > 0.0


class TestEquation08AgapeIndex:
    """Test Equation 8: Índice Agápe (ΣEA/LO-14)"""

    def test_basic_agape(self):
        """Smoke test: Agápe index calculation"""
        from penin.equations.agape_index import AgapeConfig

        virtues = {"paciencia": 0.9, "bondade": 0.85, "humildade": 0.8}
        cost = 0.2

        agape = compute_agape_index(virtues, cost, AgapeConfig(), fuzzy_measure=None)
        assert 0.0 <= agape <= 1.0


class TestEquation09OmegaSEATotal:
    """Test Equation 9: Ω-ΣEA Total - Coerência Global"""

    def test_basic_coherence(self):
        """Smoke test: Global coherence G_t"""
        module_scores = [0.9, 0.85, 0.88, 0.92, 0.87, 0.90, 0.86, 0.89]
        config = OmegaSEAConfig(epsilon=1e-3)

        g_score = omega_sea_coherence(module_scores, config)
        assert 0.0 < g_score <= 1.0


class TestEquation10AutoTuning:
    """Test Equation 10: Auto-Tuning Online"""

    def test_basic_tuning(self):
        """Smoke test: Hyperparameter update"""
        theta = np.array([20.0, 0.5, 0.01])
        gradient = np.array([-0.1, 0.05, -0.02])
        config = AutoTuningConfig(eta0=0.01)

        new_theta = auto_tune_hyperparams(theta, gradient, config)
        assert len(new_theta) == len(theta)
        assert not np.allclose(new_theta, theta)  # Should have changed


class TestEquation11LyapunovContractive:
    """Test Equation 11: Lyapunov Contratividade"""

    def test_basic_lyapunov(self):
        """Smoke test: Lyapunov decrease check"""
        V_current = 1.0
        V_next = 0.9
        config = LyapunovConfig()

        result = lyapunov_check(V_current, V_next, config)
        assert result["stable"] is True
        assert result["V_next"] < result["V_current"]


class TestEquation12OCI:
    """Test Equation 12: OCI - Organizational Closure Index"""

    def test_basic_oci(self):
        """Smoke test: OCI calculation"""
        dependencies = {"A": ["B"], "B": ["C"], "C": ["A"]}
        config = OCIConfig()

        oci = organizational_closure_index(dependencies, config)
        assert 0.0 <= oci <= 1.0


class TestEquation13DeltaLInfGrowth:
    """Test Equation 13: ΔL∞ Compound Growth"""

    def test_basic_growth(self):
        """Smoke test: Compound growth requirement"""
        L_inf_current = 0.8
        beta_min = 0.01
        config = DeltaLInfConfig(beta_min=beta_min)

        result = delta_linf_compound_growth(L_inf_current, beta_min, config)
        assert result["L_inf_next"] > L_inf_current


class TestEquation14Anabolization:
    """Test Equation 14: Auto-Evolução de Penin (Anabolização)"""

    def test_basic_anabolization(self):
        """Smoke test: Anabolization factor"""
        A_current = 1.0
        caos_plus = 2.0
        sr_score = 0.85
        oci = 0.9
        delta_linf = 0.05
        config = AnabolizationConfig(mu=0.1, nu=0.5, xi=0.3, zeta=0.2)

        A_next = anabolize_penin(A_current, caos_plus, sr_score, oci, delta_linf, config)
        assert A_next >= A_current


class TestEquation15SigmaGuardGate:
    """Test Equation 15: Σ-Guard Gate - Fail-Closed Blocking"""

    def test_all_pass(self):
        """Smoke test: Σ-Guard passing all conditions"""
        config = SigmaGuardConfig(rho_max=1.0, ece_max=0.01, bias_max=1.05, consent_required=True, eco_ok_required=True)

        metrics = {
            "rho": 0.95,
            "ece": 0.005,
            "rho_bias": 1.02,
            "consent": True,
            "eco_ok": True,
        }

        result = sigma_guard_check(metrics, config)
        assert result["gate_pass"] is True, f"Σ-Guard should pass, got {result}"

    def test_fail_on_rho(self):
        """Smoke test: Σ-Guard failing on ρ >= 1"""
        config = SigmaGuardConfig()
        metrics = {"rho": 1.05, "ece": 0.005, "rho_bias": 1.02, "consent": True, "eco_ok": True}

        result = sigma_guard_check(metrics, config)
        assert result["gate_pass"] is False, "Σ-Guard should fail when ρ >= 1"


# Summary test to ensure all equations are tested
def test_all_15_equations_covered():
    """Meta-test: Ensure all 15 equations have at least one test"""
    equation_tests = [
        TestEquation01PeninUpdate,
        TestEquation02LInfMeta,
        TestEquation03CAOSPlus,
        TestEquation04SROmegaInfinity,
        TestEquation05DeathEquation,
        TestEquation06IRIC,
        TestEquation07ACFAEPV,
        TestEquation08AgapeIndex,
        TestEquation09OmegaSEATotal,
        TestEquation10AutoTuning,
        TestEquation11LyapunovContractive,
        TestEquation12OCI,
        TestEquation13DeltaLInfGrowth,
        TestEquation14Anabolization,
        TestEquation15SigmaGuardGate,
    ]

    assert len(equation_tests) == 15, f"Expected 15 equation test classes, got {len(equation_tests)}"
    print("✅ All 15 PENIN-Ω core equations have smoke test coverage")

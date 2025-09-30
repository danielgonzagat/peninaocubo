from penin.omega.life_eq import life_equation


def test_life_eq_ok():
    res = life_equation(
        base_alpha=1e-3,
        ethics_input={"ece": 0.005, "rho_bias": 1.01, "consent": 1, "eco_ok": 1},
        risk_series={"r0": 0.9, "r1": 0.88},
        caos_components=(0.8, 0.7, 1.0, 1.0),
        sr_components=(0.85, True, 0.8, 0.82),
        linf_weights={"acc": 1, "rob": 1, "lambda_c": 0.05},
        linf_metrics={"acc": 0.8, "rob": 0.8},
        cost=0.02,
        ethical_ok_flag=True,
        G=0.9,
        dL_inf=0.02,
        thresholds={"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
    )
    assert res.ok and res.alpha_eff > 0


def test_life_eq_fail_guard():
    res = life_equation(
        base_alpha=1e-3,
        ethics_input={"ece": 0.02, "rho_bias": 1.01, "consent": 1, "eco_ok": 1},
        risk_series={"r0": 0.9, "r1": 0.88},
        caos_components=(0.8, 0.7, 1.0, 1.0),
        sr_components=(0.85, True, 0.8, 0.82),
        linf_weights={"acc": 1, "rob": 1, "lambda_c": 0.05},
        linf_metrics={"acc": 0.8, "rob": 0.8},
        cost=0.02,
        ethical_ok_flag=True,
        G=0.9,
        dL_inf=0.02,
        thresholds={"beta_min": 0.01, "theta_caos": 0.25, "tau_sr": 0.80, "theta_G": 0.85},
    )
    assert not res.ok and res.alpha_eff == 0


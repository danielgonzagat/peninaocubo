from penin.omega.life_eq import life_equation


def test_life_eq_ok():
    """Test life equation with valid parameters - should pass all gates"""
    res = life_equation(
        base_alpha=1e-3,
        # Ethics parameters
        ece=0.005,
        rho_bias=1.01,
        consent=True,
        eco_ok=True,
        # Risk
        risk_rho=0.9,
        # CAOS components
        C=0.8,
        A=0.7,
        O=1.0,
        S=1.0,
        # SR
        sr=0.85,
        # L∞
        L_inf=0.8,
        dL_inf=0.02,
        # Global coherence
        G=0.9,
        # Thresholds
        beta_min=0.01,
        theta_caos=0.25,
        tau_sr=0.80,
        theta_G=0.85,
    )
    assert res.ok and res.alpha_eff > 0


def test_life_eq_fail_guard():
    """Test life equation with bad ethics - should fail ethics gate"""
    res = life_equation(
        base_alpha=1e-3,
        # Ethics parameters - ECE too high (0.02 > 0.01)
        ece=0.02,
        rho_bias=1.01,
        consent=True,
        eco_ok=True,
        # Risk
        risk_rho=0.9,
        # CAOS components
        C=0.8,
        A=0.7,
        O=1.0,
        S=1.0,
        # SR
        sr=0.85,
        # L∞
        L_inf=0.8,
        dL_inf=0.02,
        # Global coherence
        G=0.9,
        # Thresholds
        beta_min=0.01,
        theta_caos=0.25,
        tau_sr=0.80,
        theta_G=0.85,
    )
    assert not res.ok and res.alpha_eff == 0

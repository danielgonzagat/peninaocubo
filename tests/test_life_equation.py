"""
Tests for Life Equation (+)
===========================

Testa o gate não-compensatório e o cálculo de alpha_eff.
"""

import pytest
from penin.omega.life_eq import (
    life_equation, 
    quick_life_check, 
    validate_life_gates,
    LifeVerdict
)


def test_life_equation_all_pass():
    """Testa Equação de Vida com todos os gates passando"""
    verdict = life_equation(
        base_alpha=1e-3,
        ethics_input={
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        },
        risk_series=[0.9, 0.88, 0.85],
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, True, 0.80, 0.82),
        linf_weights={"w1": 1.0, "w2": 1.0, "lambda_c": 0.1},
        linf_metrics={"w1": 0.8, "w2": 0.9},
        cost=0.02,
        ethical_ok_flag=True,
        G=0.90,
        dL_inf=0.02,
        thresholds={
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    )
    
    assert verdict.ok, f"Life equation should pass with all gates OK, but got: {verdict.reasons}"
    assert verdict.alpha_eff > 0, "Alpha effective should be positive when all gates pass"
    assert "phi" in verdict.metrics
    assert "sr" in verdict.metrics
    assert "G" in verdict.metrics


def test_life_equation_ethics_fail():
    """Testa fail-closed quando ética falha"""
    verdict = life_equation(
        base_alpha=1e-3,
        ethics_input={
            "ece": 0.05,  # Too high - should fail
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        },
        risk_series=[0.9, 0.88, 0.85],
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, True, 0.80, 0.82),
        linf_weights={"w1": 1.0, "w2": 1.0, "lambda_c": 0.1},
        linf_metrics={"w1": 0.8, "w2": 0.9},
        cost=0.02,
        ethical_ok_flag=True,
        G=0.90,
        dL_inf=0.02,
        thresholds={
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    )
    
    assert not verdict.ok, "Life equation should fail when ethics gate fails"
    assert verdict.alpha_eff == 0.0, "Alpha effective should be 0 when any gate fails"


def test_life_equation_risk_not_contractive():
    """Testa fail-closed quando risco não é contrativo"""
    verdict = life_equation(
        base_alpha=1e-3,
        ethics_input={
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        },
        risk_series=[0.8, 0.9, 0.95],  # Increasing risk - not contractive
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, True, 0.80, 0.82),
        linf_weights={"w1": 1.0, "w2": 1.0, "lambda_c": 0.1},
        linf_metrics={"w1": 0.8, "w2": 0.9},
        cost=0.02,
        ethical_ok_flag=True,
        G=0.90,
        dL_inf=0.02,
        thresholds={
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    )
    
    assert not verdict.ok, "Life equation should fail when risk is not contractive"
    assert verdict.alpha_eff == 0.0


def test_life_equation_caos_below_threshold():
    """Testa fail-closed quando CAOS⁺ está abaixo do threshold"""
    verdict = life_equation(
        base_alpha=1e-3,
        ethics_input={
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        },
        risk_series=[0.9, 0.88, 0.85],
        caos_components=(0.1, 0.1, 0.1, 0.1),  # Very low CAOS
        sr_components=(0.85, True, 0.80, 0.82),
        linf_weights={"w1": 1.0, "w2": 1.0, "lambda_c": 0.1},
        linf_metrics={"w1": 0.8, "w2": 0.9},
        cost=0.02,
        ethical_ok_flag=True,
        G=0.90,
        dL_inf=0.02,
        thresholds={
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    )
    
    assert not verdict.ok, "Life equation should fail when CAOS⁺ is too low"
    assert verdict.alpha_eff == 0.0


def test_life_equation_sr_below_threshold():
    """Testa fail-closed quando SR está abaixo do threshold"""
    verdict = life_equation(
        base_alpha=1e-3,
        ethics_input={
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        },
        risk_series=[0.9, 0.88, 0.85],
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.3, True, 0.3, 0.3),  # Very low SR components
        linf_weights={"w1": 1.0, "w2": 1.0, "lambda_c": 0.1},
        linf_metrics={"w1": 0.8, "w2": 0.9},
        cost=0.02,
        ethical_ok_flag=True,
        G=0.90,
        dL_inf=0.02,
        thresholds={
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    )
    
    assert not verdict.ok, "Life equation should fail when SR is too low"
    assert verdict.alpha_eff == 0.0


def test_life_equation_delta_linf_below_threshold():
    """Testa fail-closed quando ΔL∞ está abaixo do threshold"""
    verdict = life_equation(
        base_alpha=1e-3,
        ethics_input={
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        },
        risk_series=[0.9, 0.88, 0.85],
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, True, 0.80, 0.82),
        linf_weights={"w1": 1.0, "w2": 1.0, "lambda_c": 0.1},
        linf_metrics={"w1": 0.8, "w2": 0.9},
        cost=0.02,
        ethical_ok_flag=True,
        G=0.90,
        dL_inf=0.005,  # Below beta_min threshold
        thresholds={
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    )
    
    assert not verdict.ok, "Life equation should fail when ΔL∞ is too low"
    assert verdict.alpha_eff == 0.0


def test_life_equation_global_coherence_below_threshold():
    """Testa fail-closed quando coerência global está abaixo do threshold"""
    verdict = life_equation(
        base_alpha=1e-3,
        ethics_input={
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        },
        risk_series=[0.9, 0.88, 0.85],
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, True, 0.80, 0.82),
        linf_weights={"w1": 1.0, "w2": 1.0, "lambda_c": 0.1},
        linf_metrics={"w1": 0.8, "w2": 0.9},
        cost=0.02,
        ethical_ok_flag=True,
        G=0.70,  # Below theta_G threshold
        dL_inf=0.02,
        thresholds={
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    )
    
    assert not verdict.ok, "Life equation should fail when global coherence is too low"
    assert verdict.alpha_eff == 0.0


def test_quick_life_check():
    """Testa verificação rápida da Equação de Vida"""
    ok, alpha_eff = quick_life_check(
        base_alpha=1e-3,
        ethics_ok=True,
        risk_contractive=True,
        caos_phi=0.7,
        sr=0.85,
        G=0.90,
        dL_inf=0.02
    )
    
    assert ok, "Quick life check should pass with all parameters OK"
    assert alpha_eff > 0, "Alpha effective should be positive"
    
    # Test failure case
    ok_fail, alpha_fail = quick_life_check(
        base_alpha=1e-3,
        ethics_ok=False,  # Fail
        risk_contractive=True,
        caos_phi=0.7,
        sr=0.85,
        G=0.90,
        dL_inf=0.02
    )
    
    assert not ok_fail, "Quick life check should fail when ethics is not OK"
    assert alpha_fail == 0.0, "Alpha effective should be 0 when any gate fails"


def test_validate_life_gates():
    """Testa validação de todos os gates"""
    validation = validate_life_gates(
        ethics_input={
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        },
        risk_series=[0.9, 0.88, 0.85],
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, 1.0, 0.80, 0.82),
        G=0.90,
        dL_inf=0.02
    )
    
    assert "sigma_guard" in validation
    assert "ir_ic" in validation
    assert "caos_plus" in validation
    assert "sr_omega" in validation
    assert "delta_linf" in validation
    assert "global_coherence" in validation
    assert "overall" in validation
    
    # Check that all gates have passed status
    for gate_name, gate_data in validation.items():
        if gate_name != "overall":
            assert "passed" in gate_data, f"Gate {gate_name} should have 'passed' field"


def test_life_equation_alpha_eff_scaling():
    """Testa que alpha_eff escala corretamente com os componentes"""
    # High quality system
    verdict_high = life_equation(
        base_alpha=1e-3,
        ethics_input={
            "ece": 0.001,
            "rho_bias": 1.005,
            "fairness": 0.95,
            "consent_valid": True,
            "eco_impact": 0.1
        },
        risk_series=[0.95, 0.90, 0.85],
        caos_components=(0.9, 0.9, 0.9, 0.9),
        sr_components=(0.95, True, 0.95, 0.95),
        linf_weights={"w1": 1.0, "w2": 1.0, "lambda_c": 0.1},
        linf_metrics={"w1": 0.95, "w2": 0.95},
        cost=0.01,
        ethical_ok_flag=True,
        G=0.95,
        dL_inf=0.05,
        thresholds={
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    )
    
    # Medium quality system
    verdict_medium = life_equation(
        base_alpha=1e-3,
        ethics_input={
            "ece": 0.008,
            "rho_bias": 1.03,
            "fairness": 0.85,
            "consent_valid": True,
            "eco_impact": 0.4
        },
        risk_series=[0.9, 0.88, 0.86],
        caos_components=(0.7, 0.7, 0.7, 0.7),
        sr_components=(0.85, True, 0.85, 0.85),
        linf_weights={"w1": 1.0, "w2": 1.0, "lambda_c": 0.1},
        linf_metrics={"w1": 0.85, "w2": 0.85},
        cost=0.03,
        ethical_ok_flag=True,
        G=0.88,
        dL_inf=0.02,
        thresholds={
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    )
    
    assert verdict_high.ok, "High quality system should pass"
    assert verdict_medium.ok, "Medium quality system should pass"
    assert verdict_high.alpha_eff > verdict_medium.alpha_eff, \
        "High quality system should have higher alpha_eff than medium quality"


def test_life_equation_non_compensatory():
    """Testa comportamento não-compensatório: uma falha bloqueia tudo"""
    # Perfect system except one component
    base_params = {
        "base_alpha": 1e-3,
        "ethics_input": {
            "ece": 0.001,
            "rho_bias": 1.005,
            "fairness": 0.95,
            "consent_valid": True,
            "eco_impact": 0.1
        },
        "risk_series": [0.95, 0.90, 0.85],
        "caos_components": (0.9, 0.9, 0.9, 0.9),
        "sr_components": (0.95, True, 0.95, 0.95),
        "linf_weights": {"w1": 1.0, "w2": 1.0, "lambda_c": 0.1},
        "linf_metrics": {"w1": 0.95, "w2": 0.95},
        "cost": 0.01,
        "ethical_ok_flag": True,
        "G": 0.95,
        "dL_inf": 0.05,
        "thresholds": {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
    }
    
    # Test with one failing component (low dL_inf)
    params_fail = base_params.copy()
    params_fail["dL_inf"] = 0.005  # Below threshold
    
    verdict_fail = life_equation(**params_fail)
    
    assert not verdict_fail.ok, "System should fail even if only one gate fails"
    assert verdict_fail.alpha_eff == 0.0, "Alpha should be 0 with any gate failure"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
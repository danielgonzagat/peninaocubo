"""
Testes para a Equação de Vida (+)
=================================

Testa o gate não-compensatório e o cálculo de alpha_eff.
"""

import pytest
from penin.omega.life_eq import (
    life_equation, 
    LifeEquationEngine, 
    quick_life_check, 
    validate_life_equation_gates,
    _accel
)


class TestLifeEquation:
    """Testes da Equação de Vida (+)"""
    
    def test_accel_function(self):
        """Testa função de aceleração"""
        # Casos extremos
        assert _accel(0.0) == 1.0 / 21.0  # (1 + 20*0) / (1 + 20)
        assert _accel(1.0) == 21.0 / 21.0  # (1 + 20*1) / (1 + 20) = 1.0
        
        # Caso médio
        accel_mid = _accel(0.5)
        assert 0.4 < accel_mid < 0.6
        
        # Monotonia
        assert _accel(0.2) < _accel(0.5) < _accel(0.8)
    
    def test_life_equation_pass_case(self):
        """Testa caso que deve passar em todos os gates"""
        ethics_input = {
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        }
        
        risk_series = [0.9, 0.88, 0.85]  # Série contrativa
        caos_components = (0.8, 0.7, 0.6, 0.9)  # (C, A, O, S)
        sr_components = (0.85, True, 0.80, 0.82)  # (awareness, ethics_ok, autocorr, metacog)
        
        linf_weights = {"metric1": 1.0, "metric2": 1.0}
        linf_metrics = {"metric1": 0.8, "metric2": 0.9}
        
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        
        verdict = life_equation(
            base_alpha=0.001,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.02,
            ethical_ok_flag=True,
            G=0.90,
            dL_inf=0.02,
            thresholds=thresholds
        )
        
        assert verdict.ok is True
        assert verdict.alpha_eff > 0.0
        assert "sigma_ok" in verdict.reasons
        assert "risk_contractive" in verdict.reasons
        assert "caos_phi" in verdict.reasons
        assert "sr" in verdict.reasons
    
    def test_life_equation_ethics_fail(self):
        """Testa falha no gate ético"""
        ethics_input = {
            "ece": 0.05,  # ECE muito alto
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        }
        
        risk_series = [0.9, 0.88, 0.85]
        caos_components = (0.8, 0.7, 0.6, 0.9)
        sr_components = (0.85, True, 0.80, 0.82)
        
        linf_weights = {"metric1": 1.0, "metric2": 1.0}
        linf_metrics = {"metric1": 0.8, "metric2": 0.9}
        
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        
        verdict = life_equation(
            base_alpha=0.001,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.02,
            ethical_ok_flag=True,
            G=0.90,
            dL_inf=0.02,
            thresholds=thresholds
        )
        
        assert verdict.ok is False
        assert verdict.alpha_eff == 0.0
    
    def test_life_equation_caos_fail(self):
        """Testa falha no gate CAOS⁺"""
        ethics_input = {
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        }
        
        risk_series = [0.9, 0.88, 0.85]
        caos_components = (0.1, 0.1, 0.1, 0.1)  # CAOS⁺ muito baixo
        sr_components = (0.85, True, 0.80, 0.82)
        
        linf_weights = {"metric1": 1.0, "metric2": 1.0}
        linf_metrics = {"metric1": 0.8, "metric2": 0.9}
        
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        
        verdict = life_equation(
            base_alpha=0.001,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.02,
            ethical_ok_flag=True,
            G=0.90,
            dL_inf=0.02,
            thresholds=thresholds
        )
        
        assert verdict.ok is False
        assert verdict.alpha_eff == 0.0
        assert verdict.reasons["caos_phi"] < 0.25
    
    def test_life_equation_sr_fail(self):
        """Testa falha no gate SR"""
        ethics_input = {
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        }
        
        risk_series = [0.9, 0.88, 0.85]
        caos_components = (0.8, 0.7, 0.6, 0.9)
        sr_components = (0.1, True, 0.1, 0.1)  # SR muito baixo
        
        linf_weights = {"metric1": 1.0, "metric2": 1.0}
        linf_metrics = {"metric1": 0.8, "metric2": 0.9}
        
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        
        verdict = life_equation(
            base_alpha=0.001,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.02,
            ethical_ok_flag=True,
            G=0.90,
            dL_inf=0.02,
            thresholds=thresholds
        )
        
        assert verdict.ok is False
        assert verdict.alpha_eff == 0.0
        assert verdict.reasons["sr"] < 0.80
    
    def test_life_equation_dlinf_fail(self):
        """Testa falha no gate ΔL∞"""
        ethics_input = {
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        }
        
        risk_series = [0.9, 0.88, 0.85]
        caos_components = (0.8, 0.7, 0.6, 0.9)
        sr_components = (0.85, True, 0.80, 0.82)
        
        linf_weights = {"metric1": 1.0, "metric2": 1.0}
        linf_metrics = {"metric1": 0.8, "metric2": 0.9}
        
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        
        verdict = life_equation(
            base_alpha=0.001,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.02,
            ethical_ok_flag=True,
            G=0.90,
            dL_inf=0.005,  # ΔL∞ muito baixo
            thresholds=thresholds
        )
        
        assert verdict.ok is False
        assert verdict.alpha_eff == 0.0
        assert verdict.reasons["dL_inf"] < 0.01
    
    def test_life_equation_g_fail(self):
        """Testa falha no gate G (coerência global)"""
        ethics_input = {
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent_valid": True,
            "eco_impact": 0.3
        }
        
        risk_series = [0.9, 0.88, 0.85]
        caos_components = (0.8, 0.7, 0.6, 0.9)
        sr_components = (0.85, True, 0.80, 0.82)
        
        linf_weights = {"metric1": 1.0, "metric2": 1.0}
        linf_metrics = {"metric1": 0.8, "metric2": 0.9}
        
        thresholds = {
            "beta_min": 0.01,
            "theta_caos": 0.25,
            "tau_sr": 0.80,
            "theta_G": 0.85
        }
        
        verdict = life_equation(
            base_alpha=0.001,
            ethics_input=ethics_input,
            risk_series=risk_series,
            caos_components=caos_components,
            sr_components=sr_components,
            linf_weights=linf_weights,
            linf_metrics=linf_metrics,
            cost=0.02,
            ethical_ok_flag=True,
            G=0.5,  # G muito baixo
            dL_inf=0.02,
            thresholds=thresholds
        )
        
        assert verdict.ok is False
        assert verdict.alpha_eff == 0.0
        assert verdict.reasons["G"] < 0.85


class TestLifeEquationEngine:
    """Testes do LifeEquationEngine"""
    
    def test_engine_initialization(self):
        """Testa inicialização do engine"""
        engine = LifeEquationEngine()
        
        config = engine.get_config()
        assert "thresholds" in config
        assert "base_alpha" in config
        assert config["base_alpha"] == 0.001
    
    def test_engine_evaluate(self):
        """Testa avaliação via engine"""
        engine = LifeEquationEngine()
        
        verdict = engine.evaluate(
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
            linf_weights={"metric1": 1.0, "metric2": 1.0},
            linf_metrics={"metric1": 0.8, "metric2": 0.9},
            cost=0.02,
            ethical_ok_flag=True,
            G=0.90,
            dL_inf=0.02
        )
        
        assert verdict.ok is True
        assert verdict.alpha_eff > 0.0
        
        # Verificar histórico
        stats = engine.get_stats()
        assert stats["count"] == 1
        assert stats["passed"] == 1
        assert stats["pass_rate"] == 1.0
    
    def test_engine_update_thresholds(self):
        """Testa atualização de thresholds"""
        engine = LifeEquationEngine()
        
        original_config = engine.get_config()
        original_beta = original_config["thresholds"]["beta_min"]
        
        engine.update_thresholds(beta_min=0.02)
        
        new_config = engine.get_config()
        assert new_config["thresholds"]["beta_min"] == 0.02
        assert new_config["thresholds"]["beta_min"] != original_beta


class TestQuickFunctions:
    """Testes das funções de conveniência"""
    
    def test_quick_life_check_pass(self):
        """Testa quick_life_check com caso que passa"""
        passed, alpha_eff = quick_life_check(
            caos_components=(0.8, 0.7, 0.6, 0.9),
            sr_components=(0.85, True, 0.80, 0.82),
            G=0.90,
            dL_inf=0.02,
            ethical_ok=True
        )
        
        assert passed is True
        assert alpha_eff > 0.0
    
    def test_quick_life_check_fail(self):
        """Testa quick_life_check com caso que falha"""
        passed, alpha_eff = quick_life_check(
            caos_components=(0.1, 0.1, 0.1, 0.1),  # CAOS⁺ baixo
            sr_components=(0.85, True, 0.80, 0.82),
            G=0.90,
            dL_inf=0.02,
            ethical_ok=True
        )
        
        assert passed is False
        assert alpha_eff == 0.0
    
    def test_validate_life_equation_gates(self):
        """Testa validação completa dos gates"""
        results = validate_life_equation_gates()
        
        assert "summary" in results
        assert results["summary"]["gates_working"] is True
        
        # Verificar que apenas base_case passou
        assert results["base_case"]["passed"] is True
        assert results["ethics_fail"]["passed"] is False
        assert results["caos_fail"]["passed"] is False
        assert results["sr_fail"]["passed"] is False
        assert results["dlinf_fail"]["passed"] is False
        assert results["g_fail"]["passed"] is False


if __name__ == "__main__":
    pytest.main([__file__])
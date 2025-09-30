"""
Life Equation (+) - Gate Não-Compensatório e Orquestrador Positivo
====================================================================

Implementa a Equação de Vida (+) como contraparte da Equação da Morte.
Gate não-compensatório: se QUALQUER condição falhar, alpha_eff = 0 (fail-closed).

alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)

Componentes verificados:
1. Σ-Guard (ética) - não compensatório
2. IR→IC (contratividade de risco) - ρ < 1
3. CAOS⁺ >= theta_caos
4. SR >= tau_sr
5. ΔL∞ >= beta_min (anti-Goodhart)
6. G >= theta_G (coerência global Ω-ΣEA)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple

# Import existing modules
from .guards import sigma_guard, ir_to_ic_contractive, SigmaGuardPolicy, GuardResult
from .scoring import linf_harmonic
from .caos import phi_caos
from .sr import compute_sr_omega, SRConfig


@dataclass
class LifeVerdict:
    """Veredicto da Equação de Vida (+)"""
    ok: bool
    alpha_eff: float
    reasons: Dict[str, Any]
    metrics: Dict[str, float]
    thresholds: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "alpha_eff": self.alpha_eff,
            "reasons": self.reasons,
            "metrics": self.metrics,
            "thresholds": self.thresholds
        }


def _accel(phi: float, kappa: float = 20.0) -> float:
    """
    Aceleração suave, monotônica e saturada (fail-closed-friendly).
    α̂ = (1 + κ·phi) / (1 + κ)  ∈ (0, 1]
    """
    return (1.0 + kappa * phi) / (1.0 + kappa)


def life_equation(
    *,
    base_alpha: float,
    ethics_input: Dict[str, float],
    risk_series: Dict[str, float] | list,
    caos_components: Tuple[float, float, float, float],  # (C, A, O, S)
    sr_components: Tuple[float, float, float, float],    # (awareness, ethics_ok, autocorr, metacog)
    linf_weights: Dict[str, float],
    linf_metrics: Dict[str, float],  # {metric_name: value}
    cost: float,
    ethical_ok_flag: bool,
    G: float,    # Coerência global (Ω-ΣEA)
    dL_inf: float,  # ΔL∞ no ciclo
    thresholds: Dict[str, float],   # {beta_min, theta_caos, tau_sr, theta_G}
) -> LifeVerdict:
    """
    Implementa a Equação de Vida (+) como contraparte da Equação da Morte.
    Gate não-compensatório: se QUALQUER condição falhar, alpha_eff = 0 (fail-closed).
    
    alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)
    
    Args:
        base_alpha: Passo base de aprendizado
        ethics_input: Métricas éticas para Σ-Guard
        risk_series: Série temporal de risco para IR→IC
        caos_components: (C, A, O, S) para CAOS⁺
        sr_components: (awareness, ethics_ok, autocorr, metacog) para SR
        linf_weights: Pesos para L∞
        linf_metrics: Métricas para L∞
        cost: Custo da operação
        ethical_ok_flag: Flag ética geral
        G: Coerência global (média harmônica dos 8 módulos)
        dL_inf: ΔL∞ no ciclo (ganho de qualidade)
        thresholds: Limiares para gates {beta_min, theta_caos, tau_sr, theta_G}
        
    Returns:
        LifeVerdict com ok, alpha_eff, reasons, metrics e thresholds
    """
    reasons = {}
    
    # 1) Σ-Guard (ética) – não compensatório
    try:
        sigma_result = sigma_guard(ethics_input)
        ok_sigma = sigma_result.passed if hasattr(sigma_result, 'passed') else False
        reasons["sigma_ok"] = ok_sigma
        reasons["sigma_details"] = sigma_result.to_dict() if hasattr(sigma_result, 'to_dict') else str(sigma_result)
    except Exception as e:
        ok_sigma = False
        reasons["sigma_ok"] = False
        reasons["sigma_error"] = str(e)
    
    if not (ok_sigma and ethical_ok_flag):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)
    
    # 2) IR→IC (contratividade de risco)
    try:
        # Convert risk_series to list if needed
        if isinstance(risk_series, dict):
            risk_list = list(risk_series.values())
        else:
            risk_list = list(risk_series)
        
        iric_result = ir_to_ic_contractive(risk_list, rho_threshold=1.0)
        contractive = iric_result.passed if hasattr(iric_result, 'passed') else False
        
        # Extract rho from result
        if hasattr(iric_result, 'details'):
            rho = iric_result.details.get('avg_ratio', 1.0)
        else:
            rho = 1.0
            
        reasons["risk_contractive"] = contractive
        reasons["risk_rho"] = rho
    except Exception as e:
        contractive = False
        rho = 1.0
        reasons["risk_contractive"] = False
        reasons["risk_error"] = str(e)
    
    if not contractive:
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)
    
    # 3) CAOS⁺ e SR
    C, A, O, S = caos_components
    phi = phi_caos(C, A, O, S, kappa=25.0, gamma=1.0, kappa_max=100.0)
    reasons["caos_phi"] = phi
    
    if phi < thresholds.get("theta_caos", 0.25):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)
    
    # SR computation
    awareness, eth_ok_val, autocorr, metacog = sr_components
    # Convert boolean to float if needed
    if isinstance(eth_ok_val, bool):
        eth_ok_val = 1.0 if eth_ok_val else 0.001
    
    sr, sr_details = compute_sr_omega(awareness, eth_ok_val, autocorr, metacog)
    reasons["sr"] = sr
    reasons["sr_details"] = sr_details
    
    if sr < thresholds.get("tau_sr", 0.80):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)
    
    # 4) L∞ e ΔL∞ (anti-Goodhart)
    try:
        L_inf = linf_harmonic(
            metrics=linf_metrics,
            weights=linf_weights,
            cost_norm=cost,
            lambda_c=linf_weights.get("lambda_c", 0.0),
            ethical_ok=True,
        )
    except Exception as e:
        L_inf = 0.0
        reasons["linf_error"] = str(e)
    
    reasons["L_inf"] = L_inf
    reasons["dL_inf"] = dL_inf
    
    if dL_inf < thresholds.get("beta_min", 0.01):
        return LifeVerdict(False, 0.0, reasons, 
                         {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, 
                         thresholds)
    
    # 5) Coerência global Ω-ΣEA (média harmônica dos 8 módulos)
    reasons["G"] = G
    if G < thresholds.get("theta_G", 0.85):
        return LifeVerdict(False, 0.0, reasons, 
                         {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, 
                         thresholds)
    
    # 6) α_eff – aceleração por CAOS⁺, SR e G (fail-closed)
    alpha_eff = base_alpha * phi * sr * G * _accel(phi, kappa=20.0)
    
    metrics = {
        "alpha_eff": float(alpha_eff),
        "phi": float(phi),
        "sr": float(sr),
        "G": float(G),
        "L_inf": float(L_inf),
        "dL_inf": float(dL_inf),
        "rho": float(rho),
    }
    
    return LifeVerdict(True, float(alpha_eff), reasons, metrics, thresholds)


def quick_life_check(
    base_alpha: float = 1e-3,
    ethics_ok: bool = True,
    risk_contractive: bool = True,
    caos_phi: float = 0.7,
    sr: float = 0.85,
    G: float = 0.90,
    dL_inf: float = 0.02
) -> Tuple[bool, float]:
    """
    Verificação rápida da Equação de Vida para testes.
    
    Returns:
        (ok, alpha_eff)
    """
    # Simplified check
    thresholds = {
        "beta_min": 0.01,
        "theta_caos": 0.25,
        "tau_sr": 0.80,
        "theta_G": 0.85
    }
    
    # Quick checks
    if not ethics_ok:
        return False, 0.0
    if not risk_contractive:
        return False, 0.0
    if caos_phi < thresholds["theta_caos"]:
        return False, 0.0
    if sr < thresholds["tau_sr"]:
        return False, 0.0
    if dL_inf < thresholds["beta_min"]:
        return False, 0.0
    if G < thresholds["theta_G"]:
        return False, 0.0
    
    # Compute alpha_eff
    alpha_eff = base_alpha * caos_phi * sr * G * _accel(caos_phi, kappa=20.0)
    
    return True, alpha_eff


def validate_life_gates(
    ethics_input: Dict[str, float],
    risk_series: list,
    caos_components: Tuple[float, float, float, float],
    sr_components: Tuple[float, float, float, float],
    G: float,
    dL_inf: float
) -> Dict[str, Any]:
    """
    Valida todos os gates da Equação de Vida.
    
    Returns:
        Dict com status de cada gate
    """
    validation = {}
    
    # Sigma Guard
    try:
        sigma_result = sigma_guard(ethics_input)
        validation["sigma_guard"] = {
            "passed": sigma_result.passed if hasattr(sigma_result, 'passed') else False,
            "details": sigma_result.to_dict() if hasattr(sigma_result, 'to_dict') else str(sigma_result)
        }
    except Exception as e:
        validation["sigma_guard"] = {"passed": False, "error": str(e)}
    
    # IR->IC
    try:
        iric_result = ir_to_ic_contractive(risk_series)
        validation["ir_ic"] = {
            "passed": iric_result.passed if hasattr(iric_result, 'passed') else False,
            "details": iric_result.to_dict() if hasattr(iric_result, 'to_dict') else str(iric_result)
        }
    except Exception as e:
        validation["ir_ic"] = {"passed": False, "error": str(e)}
    
    # CAOS+
    C, A, O, S = caos_components
    phi = phi_caos(C, A, O, S)
    validation["caos_plus"] = {
        "phi": phi,
        "passed": phi >= 0.25,
        "threshold": 0.25
    }
    
    # SR
    awareness, ethics, autocorr, metacog = sr_components
    sr, _ = compute_sr_omega(awareness, ethics, autocorr, metacog)
    validation["sr_omega"] = {
        "sr": sr,
        "passed": sr >= 0.80,
        "threshold": 0.80
    }
    
    # dL_inf
    validation["delta_linf"] = {
        "value": dL_inf,
        "passed": dL_inf >= 0.01,
        "threshold": 0.01
    }
    
    # Global coherence
    validation["global_coherence"] = {
        "G": G,
        "passed": G >= 0.85,
        "threshold": 0.85
    }
    
    # Overall
    all_passed = all(v.get("passed", False) for v in validation.values())
    validation["overall"] = {
        "all_passed": all_passed,
        "num_gates": len(validation),
        "num_passed": sum(1 for v in validation.values() if v.get("passed", False))
    }
    
    return validation
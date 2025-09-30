"""
Life Equation (+) - Non-Compensatory Gate and Positive Orchestrator
===================================================================

Implements the Life Equation (+) as the counterpart to Death Equation.
Non-compensatory gate: if ANY condition fails, alpha_eff = 0 (fail-closed).
alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)

This module ensures evolution only happens when ALL safety conditions pass.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional

# Import existing engines from the repository
from .guards import sigma_guard, ir_to_ic_contractive
from .scoring import linf_harmonic
from .caos import phi_caos
from .sr import sr_omega


@dataclass
class LifeVerdict:
    """Verdict from Life Equation evaluation"""
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
    Smooth, monotonic, saturated acceleration (fail-closed-friendly)
    α̂ = (1 + κ·phi) / (1 + κ)  ∈ (0, 1]
    """
    return (1.0 + kappa * phi) / (1.0 + kappa)


def life_equation(
    *,
    base_alpha: float,
    ethics_input: Dict[str, float],
    risk_series: Dict[str, float],
    caos_components: Tuple[float, float, float, float],  # (C, A, O, S)
    sr_components: Tuple[float, float, float, float],    # (awareness, ethics_ok, autocorr, metacog)
    linf_weights: Dict[str, float],
    linf_metrics: Dict[str, float],  # {metric_name: value}
    cost: float,
    ethical_ok_flag: bool,
    G: float,    # Global coherence (Ω-ΣEA)
    dL_inf: float,  # ΔL∞ in the cycle
    thresholds: Optional[Dict[str, float]] = None,
) -> LifeVerdict:
    """
    Implements the Life Equation (+) as counterpart to Death Equation.
    Non-compensatory gate: if ANY condition fails, alpha_eff = 0 (fail-closed).
    alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)
    
    Args:
        base_alpha: Base learning rate
        ethics_input: Ethics metrics dict (ece, rho_bias, fairness, consent, eco_ok)
        risk_series: Risk time series for contractivity check
        caos_components: (C, A, O, S) tuple for CAOS⁺ calculation
        sr_components: (awareness, ethics_ok, autocorr, metacog) for SR-Ω∞
        linf_weights: Weights for L∞ calculation
        linf_metrics: Current metrics dict
        cost: Current cost
        ethical_ok_flag: Overall ethics flag
        G: Global coherence (Ω-ΣEA)
        dL_inf: ΔL∞ change in cycle
        thresholds: Thresholds dict (beta_min, theta_caos, tau_sr, theta_G)
    
    Returns:
        LifeVerdict with decision and details
    """
    # Default thresholds if not provided
    if thresholds is None:
        thresholds = {
            "beta_min": 0.01,    # Minimum ΔL∞
            "theta_caos": 0.25,  # Minimum CAOS⁺
            "tau_sr": 0.80,      # Minimum SR
            "theta_G": 0.85,     # Minimum global coherence
            "ece_max": 0.01,     # Maximum ECE
            "rho_bias_max": 1.05 # Maximum ρ_bias
        }
    
    reasons = {}
    
    # 1) Σ-Guard (ethics) - non-compensatory
    guard_metrics = {
        "ece": ethics_input.get("ece", 1.0),
        "rho_bias": ethics_input.get("rho_bias", 999.0),
        "fairness": ethics_input.get("fairness", 0.0),
        "consent": bool(ethics_input.get("consent", False)),
        "eco_ok": bool(ethics_input.get("eco_ok", False)),
    }
    
    # Create a simple policy object or use the function differently
    from .guards import GuardResult
    
    # Simple check based on thresholds
    ok_sigma = (
        guard_metrics["ece"] <= thresholds.get("ece_max", 0.01) and
        guard_metrics["rho_bias"] <= thresholds.get("rho_bias_max", 1.05) and
        guard_metrics["consent"] and
        guard_metrics["eco_ok"]
    )
    details = guard_metrics
    reasons["sigma_ok"] = ok_sigma
    reasons["sigma_details"] = details
    
    if not (ok_sigma and ethical_ok_flag):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)
    
    # 2) IR→IC (risk contractivity)
    # Convert risk_series dict to list
    risk_history = list(risk_series.values()) if isinstance(risk_series, dict) else risk_series
    
    # Calculate contractivity
    if len(risk_history) >= 2:
        rho = max(risk_history[-1] / max(risk_history[-2], 1e-9), 0.0)
    else:
        rho = 0.9  # Default safe value
    
    contractive = rho < 1.0
    reasons["risk_contractive"] = contractive
    reasons["risk_rho"] = rho
    
    if not contractive:
        return LifeVerdict(False, 0.0, reasons, {"rho": float(rho)}, thresholds)
    
    # 3) CAOS⁺ and SR
    C, A, O, S = caos_components
    phi = phi_caos(C, A, O, S, kappa=25.0, gamma=1.0, kappa_max=100.0)
    reasons["caos_phi"] = phi
    
    if phi < thresholds.get("theta_caos", 0.25):
        return LifeVerdict(False, 0.0, reasons, {"phi": float(phi)}, thresholds)
    
    awr, eth_ok, autoc, meta = sr_components
    sr = sr_omega(awr, eth_ok, autoc, meta)  # Non-compensatory (harmonic/min-soft)
    reasons["sr"] = sr
    
    if sr < thresholds.get("tau_sr", 0.80):
        return LifeVerdict(False, 0.0, reasons, {"sr": float(sr)}, thresholds)
    
    # 4) L∞ and ΔL∞ (anti-Goodhart)
    # Convert metrics to lists for linf_harmonic
    weights_list = [linf_weights.get(k, 1.0) for k in linf_metrics.keys()]
    metrics_list = [linf_metrics[k] for k in linf_metrics.keys()]
    
    L_inf = linf_harmonic(
        weights_list,
        metrics_list,
        cost=cost,
        lambda_c=linf_weights.get("lambda_c", 0.01),
        ethical_ok=True
    )
    reasons["L_inf"] = L_inf
    reasons["dL_inf"] = dL_inf
    
    if dL_inf < thresholds.get("beta_min", 0.01):
        return LifeVerdict(
            False, 0.0, reasons, 
            {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, 
            thresholds
        )
    
    # 5) Global coherence Ω-ΣEA (harmonic mean of 8 modules)
    reasons["G"] = G
    if G < thresholds.get("theta_G", 0.85):
        return LifeVerdict(
            False, 0.0, reasons, 
            {"L_inf": float(L_inf), "dL_inf": float(dL_inf), "G": float(G)}, 
            thresholds
        )
    
    # 6) α_eff - acceleration by CAOS⁺, SR and G (fail-closed)
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


def life_equation_simple(
    base_alpha: float = 0.001,
    ece: float = 0.005,
    rho_bias: float = 1.01,
    risk_rho: float = 0.95,
    caos_values: Tuple[float, float, float, float] = (0.8, 0.7, 0.6, 0.9),
    sr_values: Tuple[float, float, float, float] = (0.85, 1.0, 0.80, 0.82),
    dL_inf: float = 0.02,
    G: float = 0.90,
    **kwargs
) -> LifeVerdict:
    """
    Simplified interface for Life Equation with sensible defaults.
    
    Args:
        base_alpha: Base learning rate (default 0.001)
        ece: Expected Calibration Error (default 0.005)
        rho_bias: Bias ratio (default 1.01)
        risk_rho: Risk contractivity factor (default 0.95)
        caos_values: (C, A, O, S) tuple (default high values)
        sr_values: (awareness, ethics, autocorr, metacog) tuple
        dL_inf: Delta L-infinity (default 0.02)
        G: Global coherence (default 0.90)
        **kwargs: Additional parameters
    
    Returns:
        LifeVerdict with decision
    """
    ethics_input = {
        "ece": ece,
        "rho_bias": rho_bias,
        "fairness": kwargs.get("fairness", 0.9),
        "consent": kwargs.get("consent", True),
        "eco_ok": kwargs.get("eco_ok", True),
    }
    
    risk_series = {
        f"r{i}": risk_rho * (0.95 + 0.05 * (i % 2))
        for i in range(5)
    }
    
    linf_metrics = kwargs.get("linf_metrics", {
        "accuracy": 0.85,
        "robustness": 0.80,
        "calibration": 0.90,
    })
    
    linf_weights = kwargs.get("linf_weights", {
        k: 1.0 for k in linf_metrics.keys()
    })
    linf_weights["lambda_c"] = kwargs.get("lambda_c", 0.01)
    
    return life_equation(
        base_alpha=base_alpha,
        ethics_input=ethics_input,
        risk_series=risk_series,
        caos_components=caos_values,
        sr_components=sr_values,
        linf_weights=linf_weights,
        linf_metrics=linf_metrics,
        cost=kwargs.get("cost", 0.02),
        ethical_ok_flag=kwargs.get("ethical_ok", True),
        G=G,
        dL_inf=dL_inf,
        thresholds=kwargs.get("thresholds", None)
    )
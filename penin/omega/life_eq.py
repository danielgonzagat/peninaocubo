"""
Life Equation (+) - Non-compensatory gate and positive evolution orchestrator
Implements alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)
Fail-closed: any gate failure → alpha_eff = 0
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple

# Import existing modules from repo
from .guards import sigma_guard, ir_to_ic_contractive
from .scoring import linf_harmonic
from .caos import phi_caos
from .sr import sr_omega


@dataclass
class LifeVerdict:
    """Result of Life Equation evaluation"""
    ok: bool
    alpha_eff: float
    reasons: Dict[str, Any]
    metrics: Dict[str, float]
    thresholds: Dict[str, float]


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
    dL_inf: float,  # ΔL∞ in cycle
    thresholds: Dict[str, float],   # {beta_min, theta_caos, tau_sr, theta_G}
) -> LifeVerdict:
    """
    Implements Life Equation (+) as counterpart to Death Equation.
    Non-compensatory gate: if ANY condition fails, alpha_eff = 0 (fail-closed).
    alpha_eff = base_alpha * φ(CAOS⁺) * SR * G * accel(φ)
    
    Parameters:
    -----------
    base_alpha: Base learning rate
    ethics_input: Ethics metrics (ece, rho_bias, fairness, consent, eco_ok)
    risk_series: Risk time series for contractiveness check
    caos_components: (C, A, O, S) for CAOS⁺ computation
    sr_components: (awareness, ethics_ok, autocorr, metacog) for SR
    linf_weights: Weights for L∞ computation
    linf_metrics: Metrics for L∞ computation
    cost: Current cost
    ethical_ok_flag: External ethics flag
    G: Global coherence across 8 modules
    dL_inf: Delta L∞ improvement
    thresholds: Gates thresholds
    
    Returns:
    --------
    LifeVerdict with ok status, alpha_eff, reasons, metrics, and thresholds
    """
    reasons = {}

    # 1) Σ-Guard (ethics) – non-compensatory
    # Prepare metrics dict for sigma_guard
    metrics = {
        "ece": ethics_input.get("ece", 1.0),
        "rho_bias": ethics_input.get("rho_bias", 999.0),
        "fairness": ethics_input.get("fairness", 0.0),
        "consent": bool(ethics_input.get("consent", 0)),
        "eco_ok": bool(ethics_input.get("eco_ok", 0))
    }
    ok_sigma = sigma_guard(metrics)
    reasons["sigma_ok"] = ok_sigma
    reasons["sigma_details"] = metrics
    if not (ok_sigma and ethical_ok_flag):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    # 2) IR→IC (risk contractiveness)
    # Convert risk_series dict to list for ir_to_ic_contractive
    risk_list = list(risk_series.values()) if isinstance(risk_series, dict) else risk_series
    contractive_result = ir_to_ic_contractive(risk_list, rho_threshold=1.0)
    reasons["risk_contractive"] = contractive_result
    # Estimate rho from risk series
    rho = max(risk_list[-1] / risk_list[0], 0.01) if len(risk_list) >= 2 else 0.9
    reasons["risk_rho"] = rho
    if not contractive_result:
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    # 3) CAOS⁺ and SR
    C, A, O, S = caos_components
    phi = phi_caos(C, A, O, S, kappa=25.0, gamma=1.0, kappa_max=100.0)  # stable (log+tanh)
    reasons["caos_phi"] = phi
    if phi < thresholds.get("theta_caos", 0.25):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    awr, eth_ok, autoc, meta = sr_components
    sr = sr_omega(awr, eth_ok, autoc, meta)  # non-compensatory (harmonic/min-soft)
    reasons["sr"] = sr
    if sr < thresholds.get("tau_sr", 0.80):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    # 4) L∞ and ΔL∞ (anti-Goodhart)
    L_inf = linf_harmonic(
        [linf_weights[k] for k in linf_metrics],
        [linf_metrics[k] for k in linf_metrics],
        cost=cost,
        lambda_c=linf_weights.get("lambda_c", 0.0),
        ethical_ok=True,
    )
    reasons["L_inf"] = L_inf
    reasons["dL_inf"] = dL_inf
    if dL_inf < thresholds.get("beta_min", 0.01):
        return LifeVerdict(False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, thresholds)

    # 5) Global coherence Ω-ΣEA (harmonic mean of 8 modules)
    reasons["G"] = G
    if G < thresholds.get("theta_G", 0.85):
        return LifeVerdict(False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, thresholds)

    # 6) α_eff – acceleration by CAOS⁺, SR and G (fail-closed)
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


def quick_test():
    """Quick test of Life Equation"""
    result = life_equation(
        base_alpha=1e-3,
        ethics_input={
            "ece": 0.005,
            "rho_bias": 1.01,
            "fairness": 0.9,
            "consent": 1,
            "eco_ok": 1,
            "thresholds": {}
        },
        risk_series={"r0": 0.9, "r1": 0.92, "r2": 0.88},
        caos_components=(0.8, 0.7, 0.6, 0.9),
        sr_components=(0.85, True, 0.80, 0.82),
        linf_weights={"w1": 1, "w2": 1, "lambda_c": 0.1},
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
        },
    )
    return result


if __name__ == "__main__":
    result = quick_test()
    print(f"Life Equation OK? {result.ok}, alpha_eff={result.alpha_eff:.6f}")
    print(f"Metrics: {result.metrics}")
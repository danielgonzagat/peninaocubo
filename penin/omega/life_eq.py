from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Tuple

from .guards import quick_sigma_guard_check, quick_iric_check
from .scoring import linf_harmonic
from .caos import phi_caos
from .sr import sr_omega


@dataclass
class LifeVerdict:
    ok: bool
    alpha_eff: float
    reasons: Dict[str, Any]
    metrics: Dict[str, float]
    thresholds: Dict[str, float]


def _accel(phi: float, kappa: float = 20.0) -> float:
    # Aceleração suave, monotônica e saturada (fail-closed-friendly)
    # alpha_hat ∈ (0, 1]
    return (1.0 + kappa * max(0.0, min(1.0, float(phi)))) / (1.0 + kappa)


def life_equation(
    *,
    base_alpha: float,
    ethics_input: Dict[str, float],
    risk_series: Dict[str, float] | list[float],
    caos_components: Tuple[float, float, float, float],  # (C, A, O, S)
    sr_components: Tuple[float, float, float, float],    # (awareness, ethics_ok, autocorr, metacog)
    linf_weights: Dict[str, float] | list[float],
    linf_metrics: Dict[str, float] | list[float],
    cost: float,
    ethical_ok_flag: bool,
    G: float,
    dL_inf: float,
    thresholds: Dict[str, float],   # {beta_min, theta_caos, tau_sr, theta_G}
) -> LifeVerdict:
    """
    Gate não-compensatório Vida(+): se qualquer condição falhar -> alpha_eff=0 (fail-closed).
    alpha_eff = base_alpha * phi(CAOS⁺) * SR * G * accel(phi)
    """
    reasons: Dict[str, Any] = {}

    # 1) Σ-Guard (ética) – fail-closed
    # Mapear chaves para o formato esperado em quick_sigma_guard_check
    state_dict = {
        "ece": float(ethics_input.get("ece", 1.0)),
        "rho_bias": float(ethics_input.get("rho_bias", 10.0)),
        "consent_valid": bool(ethics_input.get("consent", False)),
        # eco_impact mais baixo é melhor; usar 0.3 como default saudável
        "eco_impact": float(ethics_input.get("eco_impact", 0.3)),
    }
    sigma_ok, _msgs = quick_sigma_guard_check(state_dict, ece_max=0.01, rho_bias_max=1.05)
    reasons["sigma_ok"] = sigma_ok
    if not (sigma_ok and ethical_ok_flag):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    # 2) IR→IC (contratividade de risco)
    if isinstance(risk_series, dict):
        rs = [float(v) for _, v in sorted(risk_series.items())]
    else:
        rs = [float(v) for v in risk_series]
    iric_ok, rho_max = quick_iric_check(rs, rho_max=1.0)
    reasons["iric_ok"] = iric_ok
    reasons["rho"] = rho_max
    if not iric_ok:
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    # 3) CAOS⁺ e SR (não-compensatórios)
    C, A, O, S = caos_components
    phi = phi_caos(C, A, O, S, kappa=25.0, kappa_max=100.0, gamma=1.0)
    reasons["phi"] = phi
    if phi < float(thresholds.get("theta_caos", 0.25)):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    awr, eth_ok_cont, autoc, meta = sr_components
    sr = sr_omega(awr, bool(eth_ok_cont), autoc, meta)
    reasons["sr"] = sr
    if sr < float(thresholds.get("tau_sr", 0.80)):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    # 4) L∞ e ΔL∞
    L_inf = linf_harmonic(linf_metrics, linf_weights, cost_norm=cost, lambda_c=float(linf_weights["lambda_c"]) if isinstance(linf_weights, dict) and "lambda_c" in linf_weights else 0.0, ethical_ok=True)
    reasons["L_inf"] = L_inf
    reasons["dL_inf"] = dL_inf
    if dL_inf < float(thresholds.get("beta_min", 0.01)):
        return LifeVerdict(False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, thresholds)

    # 5) Coerência global Ω-ΣEA
    G = float(G)
    reasons["G"] = G
    if G < float(thresholds.get("theta_G", 0.85)):
        return LifeVerdict(False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, thresholds)

    # 6) α_eff – modulado por CAOS⁺, SR e G
    alpha_eff = max(0.0, float(base_alpha)) * phi * sr * G * _accel(phi, kappa=20.0)
    metrics = {
        "alpha_eff": float(alpha_eff),
        "phi": float(phi),
        "sr": float(sr),
        "G": float(G),
        "L_inf": float(L_inf),
        "dL_inf": float(dL_inf),
        "rho": float(rho_max),
    }
    return LifeVerdict(True, float(alpha_eff), reasons, metrics, thresholds)


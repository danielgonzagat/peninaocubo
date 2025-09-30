from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Tuple

from penin.engine.caos_plus import compute_caos_plus
from penin.math.linf import linf_score


@dataclass
class LifeVerdict:
    ok: bool
    alpha_eff: float
    reasons: Dict[str, Any]
    metrics: Dict[str, float]
    thresholds: Dict[str, float]


def _accel(phi: float, kappa: float = 20.0) -> float:
    # Smooth, monotonic, saturated acceleration in (0,1]
    return (1.0 + kappa * max(0.0, phi)) / (1.0 + kappa)


def _contractive_risk(risk_series: Dict[str, float]) -> tuple[bool, float]:
    vals = [float(x) for x in risk_series.values()] or [1.0]
    if len(vals) < 2:
        return True, 0.99
    last = vals[-1]
    prev = vals[-2]
    rho = (last + 1e-9) / (prev + 1e-9)
    return rho < 1.0, rho


def _sr_aggregate(awareness: float, ethics_ok: bool, autocorr: float, metacog: float) -> float:
    if not ethics_ok:
        return 0.0
    # Non-compensatory-ish: min-soft via weighted harmonic mean surrogate
    m = {
        "awareness": max(1e-6, awareness),
        "autocorr": max(1e-6, autocorr),
        "metacog": max(1e-6, metacog),
    }
    w = {"awareness": 1.0, "autocorr": 1.0, "metacog": 1.0}
    # harmonic mean
    num = sum(w.values())
    den = sum(w[k] / m[k] for k in m)
    return num / max(1e-6, den)


def life_equation(
    *,
    base_alpha: float,
    ethics_input: Dict[str, float],
    risk_series: Dict[str, float],
    caos_components: Tuple[float, float, float, float],  # (C, A, O, S)
    sr_components: Tuple[float, bool, float, float],     # (awareness, ethics_ok, autocorr, metacog)
    linf_weights: Dict[str, float],
    linf_metrics: Dict[str, float],  # {metric_name: value}
    cost: float,
    ethical_ok_flag: bool,
    G: float,    # global coherence
    dL_inf: float,  # ΔL∞ in the cycle
    thresholds: Dict[str, float],   # {beta_min, theta_caos, tau_sr, theta_G}
) -> LifeVerdict:
    reasons: Dict[str, Any] = {}

    # 1) Σ-Guard (ethics) – non-compensatory
    ece = float(ethics_input.get("ece", 1.0))
    rho_bias = float(ethics_input.get("rho_bias", 999.0))
    consent = bool(ethics_input.get("consent", 0))
    eco_ok = bool(ethics_input.get("eco_ok", 0))
    sigma_ok = (ece <= 0.01) and (rho_bias <= 1.05) and consent and eco_ok
    reasons["sigma_ok"] = sigma_ok
    if not (sigma_ok and ethical_ok_flag):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    # 2) IR→IC (contractivity of risk)
    contractive, rho = _contractive_risk(risk_series)
    reasons["risk_contractive"] = contractive
    reasons["risk_rho"] = rho
    if not contractive:
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    # 3) CAOS⁺ and SR
    C, A, O, S = caos_components
    phi = compute_caos_plus(C, A, O, S)
    reasons["caos_phi"] = phi
    if phi < thresholds.get("theta_caos", 0.25):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    awr, eth_ok, autoc, meta = sr_components
    sr = _sr_aggregate(awr, eth_ok, autoc, meta)
    reasons["sr"] = sr
    if sr < thresholds.get("tau_sr", 0.80):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    # 4) L∞ and ΔL∞
    L_inf = linf_score(linf_metrics, linf_weights, cost, lambda_c=linf_weights.get("lambda_c", 0.0))
    reasons["L_inf"] = L_inf
    reasons["dL_inf"] = dL_inf
    if dL_inf < thresholds.get("beta_min", 0.01):
        return LifeVerdict(False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, thresholds)

    # 5) Global coherence
    reasons["G"] = G
    if G < thresholds.get("theta_G", 0.85):
        return LifeVerdict(False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}, thresholds)

    # 6) α_eff
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


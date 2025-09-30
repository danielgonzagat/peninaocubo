from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple

from .guards import SigmaGuard, SigmaGuardPolicy, IRtoICGuard
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
    """Smooth acceleration bounded in (0,1], monotonic with phi."""
    phi_b = max(0.0, min(1.0, float(phi)))
    return (1.0 + kappa * phi_b) / (1.0 + kappa)


def _map_ethics_input_to_guard(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Map flexible ethics input keys to SigmaGuard expected keys."""
    ece = float(metrics.get("ece", metrics.get("ECE", 1.0)))
    rho_bias = float(metrics.get("rho_bias", metrics.get("rhoBias", 10.0)))
    # consent can arrive as consent or consent_valid
    consent_valid = bool(metrics.get("consent_valid", metrics.get("consent", False)))
    # eco can arrive as eco_ok True/False, convert to eco_impact (<=0.5 ok)
    if "eco_impact" in metrics:
        eco_impact = float(metrics["eco_impact"])  # 0..1
    else:
        eco_impact = 0.0 if bool(metrics.get("eco_ok", False)) else 1.0
    return {
        "ece": ece,
        "rho_bias": rho_bias,
        "consent_valid": consent_valid,
        "eco_impact": eco_impact,
    }


def life_equation(
    *,
    base_alpha: float,
    ethics_input: Dict[str, Any],
    risk_history: List[float],
    caos_components: Tuple[float, float, float, float],  # (C, A, O, S)
    sr_components: Tuple[float, bool, float, float],     # (awareness, ethics_ok, autocorr, metacog)
    linf_weights: Dict[str, float],
    linf_metrics: Dict[str, float],
    cost: float,
    G: float,                 # Global coherence proxy (0..1)
    dL_inf: float,            # ΔL∞ improvement (>= beta_min)
    thresholds: Dict[str, float] | None = None,
) -> LifeVerdict:
    """
    Equação de Vida (+) — gate não-compensatório e passo positivo.

    ok == False implies fail-closed promotion with alpha_eff = 0.0.
    """
    thr = {
        "beta_min": 0.01,
        "theta_caos": 0.25,
        "tau_sr": 0.80,
        "theta_G": 0.85,
    }
    if thresholds:
        thr.update({k: float(v) for k, v in thresholds.items()})

    reasons: Dict[str, Any] = {}

    # 1) Σ-Guard (fail-closed)
    guard_metrics = _map_ethics_input_to_guard(ethics_input)
    sg = SigmaGuard()
    sg_result, sg_viol, sg_evidence = sg.check(guard_metrics)
    reasons["sigma_guard"] = {
        "passed": sg_result.passed,
        "violations": [v.to_dict() for v in sg_viol],
    }
    if not sg_result.passed:
        return LifeVerdict(False, 0.0, reasons, {}, thr)

    # 2) IR→IC (contratividade ρ < 1)
    ir = IRtoICGuard()
    ir_result, ir_viol, ir_evidence = ir.check_contractive(risk_history)
    reasons["ir_to_ic"] = {
        "passed": ir_result.passed,
        "details": ir_evidence,
    }
    if not ir_result.passed:
        return LifeVerdict(False, 0.0, reasons, {}, thr)

    # 3) CAOS⁺ (phi proxy) e SR
    C, A, O, S = caos_components
    phi = phi_caos(C, A, O, S, kappa=25.0, kappa_max=100.0, gamma=1.0)
    reasons["phi_caos"] = phi
    if phi < thr["theta_caos"]:
        return LifeVerdict(False, 0.0, reasons, {"phi": float(phi)}, thr)

    awr, ethics_ok, autoc, meta = sr_components
    sr = sr_omega(awr, bool(ethics_ok), autoc, meta)
    reasons["sr"] = sr
    if sr < thr["tau_sr"]:
        return LifeVerdict(False, 0.0, reasons, {"phi": float(phi), "sr": float(sr)}, thr)

    # 4) L∞ e ΔL∞
    # Ensure weights cover metric keys
    w = {k: float(linf_weights.get(k, 1.0)) for k in linf_metrics.keys()}
    L_inf = linf_harmonic(metrics=linf_metrics, weights=w, cost_norm=cost, lambda_c=float(linf_weights.get("lambda_c", 0.0)), ethical_ok=True)
    reasons["L_inf"] = L_inf
    reasons["dL_inf"] = dL_inf
    if dL_inf < thr["beta_min"]:
        return LifeVerdict(False, 0.0, reasons, {"phi": float(phi), "sr": float(sr), "L_inf": float(L_inf), "dL_inf": float(dL_inf)}, thr)

    # 5) Coerência global
    reasons["G"] = G
    if G < thr["theta_G"]:
        return LifeVerdict(False, 0.0, reasons, {"phi": float(phi), "sr": float(sr), "L_inf": float(L_inf), "dL_inf": float(dL_inf), "G": float(G)}, thr)

    # 6) α_eff
    alpha_eff = float(base_alpha) * phi * sr * G * _accel(phi, kappa=20.0)
    metrics = {
        "alpha_eff": float(alpha_eff),
        "phi": float(phi),
        "sr": float(sr),
        "G": float(G),
        "L_inf": float(L_inf),
        "dL_inf": float(dL_inf),
    }
    return LifeVerdict(True, alpha_eff, reasons, metrics, thr)


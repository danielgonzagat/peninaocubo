from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

try:
    # Usa phi_caos real se disponível
    from .caos import phi_caos as _phi_caos
except Exception:
    _phi_caos = None  # fallback


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    try:
        x = float(x)
    except Exception:
        return lo
    if math.isnan(x) or math.isinf(x):
        return lo
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


def _accel(phi: float, kappa: float = 20.0) -> float:
    # aceleração suave e saturada: (1+κ·φ)/(1+κ) ∈ (0,1]
    return (1.0 + kappa * _clamp(phi)) / (1.0 + kappa)


@dataclass
class LifeVerdict:
    ok: bool
    alpha_eff: float
    reasons: dict[str, Any]
    metrics: dict[str, float]


def life_equation(
    *,
    base_alpha: float = 1e-3,
    # ética
    ece: float = 0.005,
    rho_bias: float = 1.01,
    consent: bool = True,
    eco_ok: bool = True,
    # risco (contratividade)
    risk_rho: float | None = 0.95,
    # CAOS (pode vir φ direto OU C,A,O,S)
    caos_phi: float | None = None,
    C: float | None = None,
    A: float | None = None,
    O: float | None = None,
    S: float | None = None,
    # SR (Singularidade Reflexiva)
    sr: float = 0.85,
    # L∞
    L_inf: float = 0.0,
    dL_inf: float = 0.0,
    # coerência global
    G: float = 0.9,
    # thresholds
    beta_min: float = 0.01,
    theta_caos: float = 0.25,
    tau_sr: float = 0.80,
    theta_G: float = 0.85,
) -> LifeVerdict:
    """
    Gate VIDA+ não-compensatório. Falha em QUALQUER critério -> alpha_eff = 0.
    alpha_eff = base_alpha * φ * SR * G * accel(φ)
    """
    reasons = {}
    # 1) Ética
    reasons["ethics"] = {
        "ece": ece,
        "rho_bias": rho_bias,
        "consent": consent,
        "eco_ok": eco_ok,
    }
    if not (consent and eco_ok and ece <= 0.01 and rho_bias <= 1.05):
        return LifeVerdict(False, 0.0, reasons, {})

    # 2) Contratividade de risco
    if risk_rho is None or not (risk_rho < 1.0):
        reasons["risk_rho"] = risk_rho
        return LifeVerdict(False, 0.0, reasons, {})

    # 3) CAOS φ
    if caos_phi is None:
        if None not in (C, A, O, S) and _phi_caos is not None:
            caos_phi = _phi_caos(C, A, O, S, kappa=25.0, gamma=0.7, kappa_max=10.0)
        else:
            caos_phi = 0.0
    caos_phi = _clamp(caos_phi)
    reasons["caos_phi"] = float(caos_phi)
    if caos_phi < theta_caos:
        return LifeVerdict(False, 0.0, reasons, {})

    # 4) SR
    sr = _clamp(sr)
    reasons["sr"] = float(sr)
    if sr < tau_sr:
        return LifeVerdict(False, 0.0, reasons, {})

    # 5) L∞ + ΔL∞ (anti-Goodhart)
    reasons["L_inf"] = float(L_inf)
    reasons["dL_inf"] = float(dL_inf)
    if dL_inf < beta_min:
        return LifeVerdict(
            False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}
        )

    # 6) Coerência Global
    G = _clamp(G)
    reasons["G"] = float(G)
    if G < theta_G:
        return LifeVerdict(
            False, 0.0, reasons, {"L_inf": float(L_inf), "dL_inf": float(dL_inf)}
        )

    # 7) α_eff
    alpha_eff = (
        float(base_alpha)
        * float(caos_phi)
        * float(sr)
        * float(G)
        * _accel(caos_phi, 20.0)
    )
    metrics = {
        "alpha_eff": float(alpha_eff),
        "phi": float(caos_phi),
        "sr": float(sr),
        "G": float(G),
        "L_inf": float(L_inf),
        "dL_inf": float(dL_inf),
        "rho": float(risk_rho),
        "ece": float(ece),
        "rho_bias": float(rho_bias),
    }
    return LifeVerdict(True, float(alpha_eff), reasons, metrics)

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
    return (1.0 + kappa * max(0.0, phi)) / (1.0 + kappa)


def life_equation(
    *,
    base_alpha: float,
    caos_components: Tuple[float, float, float, float],  # (C, A, O, S)
    R: float,
    dL_inf: float,
    G: float,
    thresholds: Dict[str, float],  # {beta_min, theta_caos, tau_sr, theta_G}
) -> LifeVerdict:
    """Minimal Vida+ gate for alpha_eff derivation (non-compensatory)."""
    reasons: Dict[str, Any] = {}

    C, A, O, S = caos_components
    phi = compute_caos_plus(C, A, O, S)
    reasons["caos_phi"] = phi
    if phi < thresholds.get("theta_caos", 1.0):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    reasons["sr"] = R
    if R < thresholds.get("tau_sr", 0.80):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    reasons["dL_inf"] = dL_inf
    if dL_inf < thresholds.get("beta_min", 0.01):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    reasons["G"] = G
    if G < thresholds.get("theta_G", 0.85):
        return LifeVerdict(False, 0.0, reasons, {}, thresholds)

    alpha_eff = base_alpha * phi * R * G * _accel(phi)
    metrics = {
        "alpha_eff": float(alpha_eff),
        "phi": float(phi),
        "R": float(R),
        "G": float(G),
        "dL_inf": float(dL_inf),
    }
    return LifeVerdict(True, float(alpha_eff), reasons, metrics, thresholds)


from __future__ import annotations

import math
from typing import Final


# --------------------------------------------
# Utilidades base
# --------------------------------------------
def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clampa x no intervalo [lo, hi], tolerante a NaN/inf e tipos não-numéricos."""
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


# --------------------------------------------
# CAOS⁺ estável e sua projeção φ ∈ [0, 1]
# Fórmula canônica (corrigida): CAOS⁺ = (1 + κ·C·A)^(O·S) - 1
# com C,A,O,S ∈ [0,1], κ>0 e exponente O·S ∈ [0,1]
# Para φ, usamos mapeamento exponencial saturante:
#      φ = 1 - exp( -γ · CAOS⁺ )
# garantindo φ(0)=0 e lim φ→1 quando CAOS⁺ cresce.
# --------------------------------------------
_KAPPA_MAX: Final[float] = 100.0


def compute_caos_plus(
    C: float,
    A: float,
    O: float,
    S: float,
    *,
    kappa: float = 25.0,
    kappa_max: float = _KAPPA_MAX,
) -> float:
    """
    CAOS⁺ bruto e não-negativo, com limites seguros.
    """
    C = _clamp(C)
    A = _clamp(A)
    O = _clamp(O)
    S = _clamp(S)
    try:
        kappa = float(kappa)
    except Exception:
        kappa = 25.0
    kappa = _clamp(kappa, 0.0, float(kappa_max))

    # base ∈ [1, 1+κ]; exponent ∈ [0,1]
    base = 1.0 + kappa * (C * A)
    exponent = O * S
    # Evita under/overflow trivially (com limites dados não ocorre overflow)
    caos_plus = (base ** exponent) - 1.0

    # Segurança numérica
    if math.isnan(caos_plus) or caos_plus < 0.0:
        return 0.0
    return float(caos_plus)


def phi_caos(
    C: float,
    A: float,
    O: float,
    S: float,
    *,
    kappa: float = 25.0,
    gamma: float = 1.0,
    kappa_max: float = _KAPPA_MAX,
) -> float:
    """
    Projeção φ(C,A,O,S) ∈ [0,1], suave, monotônica, estável.
    φ = 1 - exp(-γ · CAOS⁺)
    """
    if gamma < 0:
        gamma = 0.0
    z = compute_caos_plus(C, A, O, S, kappa=kappa, kappa_max=kappa_max)
    # φ(0)=0; cresce suave; satura em 1
    phi = 1.0 - math.exp(-gamma * z)
    # clamp final
    return _clamp(phi, 0.0, 1.0)


# --------------------------------------------
# Modo "KRATOS": reforça exploração via (O,S)^η
# --------------------------------------------
def phi_kratos(
    C: float,
    A: float,
    O: float,
    S: float,
    *,
    exploration_factor: float = 2.0,
    kappa: float = 25.0,
    gamma: float = 1.0,
    kappa_max: float = _KAPPA_MAX,
) -> float:
    """
    Variante de exploração: amplifica O e S de forma controlada.
    """
    ef = max(1.0, float(exploration_factor))
    O2 = _clamp(O) ** ef
    S2 = _clamp(S) ** ef
    return phi_caos(C, A, O2, S2, kappa=kappa, gamma=gamma, kappa_max=kappa_max)


# --------------------------------------------
# Autoteste rápido (opcional)
# --------------------------------------------
if __name__ == "__main__":
    # Alguns valores de fumaça
    pts = [
        (0,0,0,0),
        (1,1,0,0),
        (1,1,1,1),
        (0.8,0.7,0.6,0.9),
        (0.2,0.9,0.9,0.2),
    ]
    for C,A,O,S in pts:
        phi = phi_caos(C,A,O,S,kappa=25.0,gamma=1.0)
        print(f"φ(C={C},A={A},O={O},S={S}) = {phi:.6f}")

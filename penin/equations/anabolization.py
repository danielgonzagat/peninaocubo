"""
PENIN-Ω Equation 14: Anabolização (Auto-Evolução de Penin)
===========================================================

Fórmula:
    A_{t+1} = A_t · f_anabolize(CAOS⁺, SR, OCI, ΔL∞)

Onde f é multiplicativa e monotônica:
    f = (1 + μ·ΔL∞) · (CAOS⁺)^ν · (SR)^ξ · (OCI)^ζ

Governa aceleração/desaceleração da autoevolução.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class AnabolizationConfig:
    """Configuration for anabolization."""

    mu: float = 0.5  # ΔL∞ weight
    nu: float = 0.3  # CAOS⁺ exponent
    xi: float = 0.25  # SR exponent
    zeta: float = 0.2  # OCI exponent
    min_anabolic_rate: float = 0.5
    max_anabolic_rate: float = 2.0


def anabolize_penin(
    A_current: float,
    caos_plus: float,
    sr_score: float,
    oci_score: float,
    delta_linf: float,
    config: AnabolizationConfig | None = None,
) -> float:
    """
    Compute anabolic factor (evolution acceleration/deceleration).

    Args:
        A_current: Current anabolic rate
        caos_plus: CAOS⁺ score
        sr_score: SR-Ω∞ score
        oci_score: OCI score
        delta_linf: ΔL∞
        config: Optional configuration

    Returns:
        A_next: New anabolic rate
    """
    config = config or AnabolizationConfig()

    # Multiplicative anabolization function
    f_anabolize = (
        (1.0 + config.mu * delta_linf)
        * math.pow(caos_plus, config.nu)
        * math.pow(sr_score, config.xi)
        * math.pow(oci_score, config.zeta)
    )

    A_next = A_current * f_anabolize

    # Clamp to safe bounds
    A_next = max(config.min_anabolic_rate, min(config.max_anabolic_rate, A_next))

    return A_next


__all__ = ["AnabolizationConfig", "anabolize_penin"]

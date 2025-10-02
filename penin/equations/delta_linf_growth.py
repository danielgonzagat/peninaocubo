"""
PENIN-Ω Equation 13: Crescimento Composto de ΔL∞
==================================================

Fórmula:
    L∞^{(t+1)} ≥ L∞^{(t)} · (1 + β_min)

Define progresso mínimo obrigatório por ciclo (crescimento composto).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DeltaLInfConfig:
    """Configuration for ΔL∞ growth."""

    beta_min: float = 0.01
    compounding_enabled: bool = True


def delta_linf_compound_growth(
    L_current: float, L_next: float, config: DeltaLInfConfig | None = None
) -> tuple[bool, float]:
    """
    Check if L∞ growth meets compound threshold.

    Returns:
        (meets_threshold, actual_growth_rate)
    """
    config = config or DeltaLInfConfig()

    if L_current <= 0:
        return False, 0.0

    growth_rate = (L_next - L_current) / L_current
    meets = growth_rate >= config.beta_min

    return meets, growth_rate


__all__ = ["DeltaLInfConfig", "delta_linf_compound_growth"]

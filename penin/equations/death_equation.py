"""
PENIN-Ω Equation 5: Equação da Morte (Seleção Darwiniana)
==========================================================

Implementa gate de seleção darwiniana: elimina variantes que não entregam
ganho mínimo (ΔL∞ < β_min).

Fórmula:
    D(x) = 1  se ΔL∞(x) < β_min
         = 0  caso contrário

Onde:
- ΔL∞: Ganho na meta-função
- β_min: Limiar mínimo de melhoria (auto-ajustável)

Features:
- Auto-tuning de β_min via bandit (orçamento e risco)
- Rollback automático em caso de morte
- Quarentena de mutações falhadas
"""

from __future__ import annotations

from dataclasses import dataclass

# Re-export from canonical implementation
from penin.math.vida_morte_gates import (
    auto_tune_beta_min,
    compute_lyapunov_quadratic,
    death_gate,
    life_gate_lyapunov,
)


@dataclass
class DeathConfig:
    """Configuration for Death Gate."""

    beta_min: float = 0.01
    enable_auto_tune: bool = True
    budget_weight: float = 0.5
    risk_weight: float = 0.5


def death_gate_check(delta_linf: float, config: DeathConfig | None = None) -> bool:
    """
    Check if challenger should be killed (darwinian selection).

    Args:
        delta_linf: Change in L∞ score
        config: Optional configuration

    Returns:
        True if should kill (ΔL∞ < β_min), False if should keep

    Example:
        >>> death_gate_check(0.005)  # Below default β_min=0.01
        True
        >>> death_gate_check(0.05)   # Above threshold
        False
    """
    config = config or DeathConfig()
    return death_gate(delta_linf, config.beta_min)


__all__ = [
    "DeathConfig",
    "death_gate_check",
    "death_gate",
    "life_gate_lyapunov",
    "compute_lyapunov_quadratic",
    "auto_tune_beta_min",
]

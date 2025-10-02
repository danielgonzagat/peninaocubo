"""
PENIN-Ω Equation 11: Contratividade Lyapunov
=============================================

Implementa verificação de contratividade via função de Lyapunov.

Fórmula:
    V(I_{t+1}) < V(I_t)  e  dV/dt ≤ 0

Garante convergência e estabilidade do sistema evolutivo.

Re-exports from penin.math.vida_morte_gates and penin.math.penin_master_equation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from penin.math.vida_morte_gates import compute_lyapunov_quadratic, life_gate_lyapunov


@dataclass
class LyapunovConfig:
    """Configuration for Lyapunov contractivity check."""

    tolerance: float = 1e-6
    I_star: Any = None  # Target state


def lyapunov_check(
    I_current: dict[str, float],
    I_next: dict[str, float],
    config: LyapunovConfig | None = None,
) -> tuple[bool, float]:
    """
    Check Lyapunov contractivity: V(I_next) < V(I_current).

    Returns:
        (is_contractive, V_delta)
    """
    config = config or LyapunovConfig()
    I_star = config.I_star or {k: 0.0 for k in I_current.keys()}

    V_current = compute_lyapunov_quadratic(I_current, I_star)
    V_next = compute_lyapunov_quadratic(I_next, I_star)

    delta_V = V_next - V_current
    is_contractive = delta_V < config.tolerance

    return is_contractive, delta_V


__all__ = [
    "LyapunovConfig",
    "lyapunov_check",
    "compute_lyapunov_quadratic",
    "life_gate_lyapunov",
]

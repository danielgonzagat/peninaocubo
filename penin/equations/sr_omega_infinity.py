"""
PENIN-Ω Equation 4: SR-Ω∞ (Singularidade Reflexiva)
====================================================

Implementa a Singularidade Reflexiva SR-Ω∞ para metacognição operacional contínua.

Fórmula:
    I_{t+1} = Π_{H∩S}(I_t + α_t^{eff} · ΔL∞)
    α_t^{eff} = α_0 · φ(CAOS⁺) · R_t

Onde:
- R_t: score reflexivo (autoconsciência, ética, autocorreção, metacognição)
- φ: função de saturação (tanh)
- α_0: taxa de aprendizado base

Componentes:
- Autoconsciência: Calibração agregada
- Ética: ΣEA/IR→IC (binário 0/1)
- Autocorreção: Queda de risco agregado
- Metacognição: ΔL∞/ΔCusto

Agregação: Média harmônica (não-compensatória)
"""

from __future__ import annotations

from dataclasses import dataclass

# Re-export from canonical implementation
from penin.math.sr_omega_infinity import (
    compute_alpha_effective,
    compute_autocorrection,
    compute_awareness,
    compute_metacognition,
    compute_sr_score,
)


@dataclass
class SRConfig:
    """Configuration for SR-Ω∞ computation."""

    alpha_base: float = 0.1
    gamma_saturation: float = 0.8
    epsilon: float = 1e-6
    min_sr_threshold: float = 0.80


def compute_sr_omega_infinity(
    awareness: float, ethics_ok: bool, autocorrection: float, metacognition: float, config: SRConfig | None = None
) -> float:
    """
    Compute SR-Ω∞ score using harmonic mean.

    Args:
        awareness: Calibration score [0, 1]
        ethics_ok: ΣEA/IR→IC pass/fail
        autocorrection: Risk reduction [0, 1]
        metacognition: ΔL∞/ΔCost [0, 1]
        config: Optional configuration

    Returns:
        SR score [0, 1]

    Raises:
        ValueError: If any metric is out of [0, 1] range
    """
    config = config or SRConfig()
    return compute_sr_score(awareness, ethics_ok, autocorrection, metacognition, config.epsilon)


__all__ = [
    "SRConfig",
    "compute_sr_omega_infinity",
    "compute_sr_score",
    "compute_alpha_effective",
    "compute_awareness",
    "compute_autocorrection",
    "compute_metacognition",
]

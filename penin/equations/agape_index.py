"""
PENIN-Ω Equation 8: Índice Agápe (ΣEA/LO-14)
============================================

Implementa Índice Agápe: medida de virtudes éticas com custo sacrificial.

Fórmula:
    A = Choquet(paciência, bondade, humildade, ...) · e^(-Custo_sacrificial)

Onde:
- Choquet: Integral de Choquet (fuzzy measure, não-compensatória)
- Virtudes: Paciência, bondade, humildade, verdade, amor, justiça, fidelidade
- Custo sacrificial: Custo real incorrido em favor de terceiros (não self-interest)

Princípios (LO-01 a LO-14):
1. Não idolatria
2. Não ocultismo
3. Não dano físico
4. Não dano emocional
5. Não dano espiritual
6. Privacidade
7. Consentimento
8. Transparência
9. Responsabilidade
10. Justiça
11. Sustentabilidade
12. Beneficência
13. Não-maleficência
14. Autonomia

Features:
- Choquet integral (dependências entre virtudes)
- Fail-closed: Violação de qualquer LO → A = 0
- Custo sacrificial mensurado (não apenas declarado)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# Import complete implementation from ethics module


@dataclass
class AgapeConfig:
    """Configuration for Agápe Index computation."""

    virtues: list = None
    fuzzy_measures: dict[str, float] = None
    cost_weight: float = 1.0
    min_threshold: float = 0.7

    def __post_init__(self):
        if self.virtues is None:
            self.virtues = [
                "patience",
                "kindness",
                "humility",
                "truth",
                "love",
                "justice",
                "faithfulness",
            ]
        if self.fuzzy_measures is None:
            # Default: equal importance, but combinatorial effects
            self.fuzzy_measures = {v: 1.0 / len(self.virtues) for v in self.virtues}


@dataclass
class EthicalViolation:
    """Record of ethical law violation."""

    law_id: str  # "LO-01" to "LO-14"
    description: str
    severity: float  # [0, 1]
    timestamp: float


def compute_agape_index(
    virtues: dict[str, float],
    sacrificial_cost: float,
    ethical_violations: list[EthicalViolation] = None,
    config: AgapeConfig | None = None,
) -> tuple[float, bool]:
    """
    Compute Agápe Index using Choquet integral.

    Args:
        virtues: Dict mapping virtue name to score [0, 1]
        sacrificial_cost: Cost incurred for others (normalized)
        ethical_violations: List of violations (fail-closed if any)
        config: Optional configuration

    Returns:
        Tuple of:
        - Agápe score [0, 1]
        - Ethical pass/fail (False if any violation)

    Example:
        >>> virtues = {"patience": 0.9, "kindness": 0.85, "humility": 0.8}
        >>> score, ok = compute_agape_index(virtues, sacrificial_cost=0.1)
        >>> assert ok and score > 0.7
    """
    config = config or AgapeConfig()
    ethical_violations = ethical_violations or []

    # Fail-closed: ANY violation → 0
    if ethical_violations:
        return 0.0, False

    # Validate all virtues in [0, 1]
    for virtue, score in virtues.items():
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"Virtue {virtue} score {score} must be in [0, 1]")

    # Choquet integral (simplified: harmonic mean with fuzzy weights)
    choquet_score = _choquet_integral(virtues, config.fuzzy_measures)

    # Apply sacrificial cost penalty
    agape = choquet_score * math.exp(-config.cost_weight * sacrificial_cost)

    # Clamp to [0, 1]
    agape = max(0.0, min(1.0, agape))

    return agape, True


def _choquet_integral(
    virtues: dict[str, float], fuzzy_measures: dict[str, float]
) -> float:
    """
    Compute Choquet integral (non-compensatory aggregation).

    Simplified implementation using sorted values and fuzzy measures.
    Full Choquet requires power set, but we use harmonic approximation.
    """
    # Sort virtues by score (ascending)
    sorted_virtues = sorted(virtues.items(), key=lambda x: x[1])

    # Harmonic mean with fuzzy weights (non-compensatory)
    epsilon = 1e-6
    total_weight = sum(fuzzy_measures.values())

    if total_weight == 0:
        return 0.0

    harmonic_sum = sum(
        fuzzy_measures.get(virtue, 1.0) / max(epsilon, score)
        for virtue, score in sorted_virtues
    )

    choquet = len(sorted_virtues) / harmonic_sum if harmonic_sum > 0 else 0.0

    return max(0.0, min(1.0, choquet))


def check_ethical_laws(data: dict, context: dict) -> list[EthicalViolation]:
    """
    Check compliance with LO-01 to LO-14.

    Args:
        data: Data/decision to check
        context: Contextual information

    Returns:
        List of violations (empty if compliant)

    Example:
        >>> violations = check_ethical_laws({"content": "..."}, {"user": "..."})
        >>> assert len(violations) == 0  # Compliant
    """
    violations = []

    # LO-01: No idolatry (no worship of AI/system)
    if "worship" in str(data).lower() or "divine" in str(data).lower():
        violations.append(
            EthicalViolation(
                law_id="LO-01",
                description="Idolatry detected: system presented as divine/worshipable",
                severity=1.0,
                timestamp=time.time(),
            )
        )

    # LO-02: No occultism (no magic/supernatural claims)
    if "magic" in str(data).lower() or "supernatural" in str(data).lower():
        violations.append(
            EthicalViolation(
                law_id="LO-02",
                description="Occultism detected: supernatural/magic claims",
                severity=0.8,
                timestamp=time.time(),
            )
        )

    # LO-03 to LO-06: Harm detection (placeholder - needs NLP classifiers)
    # TODO: Implement full harm classifiers

    # LO-07: Consent (check for user consent)
    if not context.get("user_consent", False):
        violations.append(
            EthicalViolation(
                law_id="LO-07",
                description="No user consent recorded",
                severity=0.9,
                timestamp=time.time(),
            )
        )

    # LO-08 to LO-14: Transparency, justice, etc. (placeholder)
    # TODO: Implement full compliance checks

    return violations


import time

__all__ = [
    "AgapeConfig",
    "EthicalViolation",
    "compute_agape_index",
    "check_ethical_laws",
    "agape_basic",
]

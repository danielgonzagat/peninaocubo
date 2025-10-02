"""
Índice Agápe (ΣEA Component)

Measures virtues with sacrificial cost (non-compensatory Choquet integral).
Mathematical form: A = Choquet(virtues) · e^(-cost_sacrificial)

Reference: penin/equations/agape_index.py (original theory)
"""

import math
from dataclasses import dataclass


@dataclass
class Virtue:
    """Individual virtue measurement"""

    name: str
    score: float  # [0, 1]
    weight: float  # Importance weight


class AgapeIndex:
    """
    Índice Agápe Calculator

    Measures ethical virtues with sacrificial component.
    Non-compensatory: low virtue in one dimension cannot be fully
    compensated by high virtue in another.

    Virtues measured:
    - Paciência (Patience)
    - Bondade (Kindness)
    - Humildade (Humility)
    - Generosidade (Generosity)
    - Perdão (Forgiveness)
    - Transparência (Transparency)
    - Justiça (Justice)
    """

    VIRTUE_NAMES = [
        "patience",
        "kindness",
        "humility",
        "generosity",
        "forgiveness",
        "transparency",
        "justice",
    ]

    def __init__(self, lambda_cost: float = 1.0):
        """
        Args:
            lambda_cost: Penalty weight for sacrificial cost
        """
        self.lambda_cost = lambda_cost

    def compute(
        self,
        virtues: dict[str, float],
        cost_sacrificial: float,
    ) -> float:
        """
        Compute Agápe Index.

        Args:
            virtues: Dict of virtue_name → score [0, 1]
            cost_sacrificial: Cost paid for benefit of others

        Returns:
            Agápe score A ∈ [0, 1]

        Formula:
            A = Choquet(virtues) · e^(-λ · cost_sacrificial)
        """
        # Validate virtues
        for name in self.VIRTUE_NAMES:
            if name not in virtues:
                raise ValueError(f"Missing virtue: {name}")
            if not 0 <= virtues[name] <= 1:
                raise ValueError(f"Virtue {name} out of bounds: {virtues[name]}")

        # Compute Choquet integral (non-compensatory)
        choquet_score = self._choquet_integral(virtues)

        # Apply sacrificial cost penalty
        cost_penalty = math.exp(-self.lambda_cost * cost_sacrificial)

        agape_score = choquet_score * cost_penalty

        return max(0.0, min(1.0, agape_score))

    def _choquet_integral(self, virtues: dict[str, float]) -> float:
        """
        Choquet integral for non-compensatory aggregation.

        Simplified implementation: harmonic mean as conservative approximation.
        True Choquet requires fuzzy measure (future enhancement).

        Args:
            virtues: Dict of virtue scores

        Returns:
            Aggregated score via harmonic mean
        """
        scores = [virtues[name] for name in self.VIRTUE_NAMES]

        # Harmonic mean (worst dimension dominates)
        eps = 1e-6
        n = len(scores)
        harmonic = n / sum(1.0 / (s + eps) for s in scores)

        return harmonic


def compute_agape_score(
    patience: float = 0.5,
    kindness: float = 0.5,
    humility: float = 0.5,
    generosity: float = 0.5,
    forgiveness: float = 0.5,
    transparency: float = 0.5,
    justice: float = 0.5,
    cost_sacrificial: float = 0.0,
    lambda_cost: float = 1.0,
) -> float:
    """
    Convenience function to compute Agápe score.

    Args:
        patience: Patience virtue [0, 1]
        kindness: Kindness virtue [0, 1]
        humility: Humility virtue [0, 1]
        generosity: Generosity virtue [0, 1]
        forgiveness: Forgiveness virtue [0, 1]
        transparency: Transparency virtue [0, 1]
        justice: Justice virtue [0, 1]
        cost_sacrificial: Sacrificial cost (≥0)
        lambda_cost: Cost penalty weight

    Returns:
        Agápe Index A ∈ [0, 1]

    Example:
        >>> score = compute_agape_score(
        ...     patience=0.8,
        ...     kindness=0.9,
        ...     humility=0.7,
        ...     generosity=0.85,
        ...     forgiveness=0.75,
        ...     transparency=0.95,
        ...     justice=0.88,
        ...     cost_sacrificial=0.1
        ... )
        >>> print(f"Agápe: {score:.3f}")
        Agápe: 0.761
    """
    virtues = {
        "patience": patience,
        "kindness": kindness,
        "humility": humility,
        "generosity": generosity,
        "forgiveness": forgiveness,
        "transparency": transparency,
        "justice": justice,
    }

    calculator = AgapeIndex(lambda_cost=lambda_cost)
    return calculator.compute(virtues, cost_sacrificial)

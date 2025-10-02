"""
PENIN-Ω Equation 9: Ω-ΣEA Total (Coerência Global Sistêmica)
=============================================================

Implementa coerência global entre os 8 módulos principais do sistema.

Fórmula:
    G_t = (Σ_{m=1}^8 w_m / max(ε, s_m(t)))^{-1}

Onde:
- s_m(t): Score do módulo m no tempo t
- w_m: Peso do módulo m
- ε: Estabilizador numérico
- G_t: Coerência global [0, 1]

8 Módulos:
1. ΣEA/LO-14 (Ética)
2. IR→IC (Contratividade)
3. ACFA (League/EPV)
4. CAOS⁺ (Motor evolutivo)
5. SR-Ω∞ (Singularidade reflexiva)
6. Ω-META (Auto-evolução)
7. Auto-Tuning (Hiperparâmetros)
8. APIs/Router (Orquestração)

Agregação: Harmônica ponderada (bottleneck = worst module dominates)

Gate: G_t < threshold → bloqueia promoção global
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OmegaSEAConfig:
    """Configuration for Ω-ΣEA Total coherence."""

    epsilon: float = 1e-3
    min_coherence_threshold: float = 0.85
    module_weights: dict[str, float] = None

    def __post_init__(self):
        if self.module_weights is None:
            # Default: equal weights for all 8 modules
            self.module_weights = {
                "ethics_sea": 1.0 / 8,
                "contractivity_iric": 1.0 / 8,
                "acfa_league": 1.0 / 8,
                "caos_plus": 1.0 / 8,
                "sr_omega": 1.0 / 8,
                "omega_meta": 1.0 / 8,
                "auto_tuning": 1.0 / 8,
                "apis_router": 1.0 / 8,
            }


@dataclass
class ModuleHealth:
    """Health metrics for a module."""

    module_name: str
    score: float  # [0, 1]
    is_operational: bool
    last_update_timestamp: float
    errors_count: int = 0


def omega_sea_coherence(
    module_scores: dict[str, float], config: OmegaSEAConfig | None = None
) -> tuple[float, bool]:
    """
    Compute global system coherence (Ω-ΣEA Total).

    Args:
        module_scores: Dict mapping module name to score [0, 1]
        config: Optional configuration

    Returns:
        Tuple of:
        - Global coherence G_t [0, 1]
        - Gate pass/fail (True if G_t ≥ threshold)

    Raises:
        ValueError: If any score is out of [0, 1] or module missing

    Example:
        >>> scores = {
        ...     "ethics_sea": 0.95,
        ...     "contractivity_iric": 0.92,
        ...     "acfa_league": 0.88,
        ...     "caos_plus": 0.90,
        ...     "sr_omega": 0.87,
        ...     "omega_meta": 0.85,
        ...     "auto_tuning": 0.89,
        ...     "apis_router": 0.91,
        ... }
        >>> G, ok = omega_sea_coherence(scores)
        >>> assert ok and G >= 0.85
    """
    config = config or OmegaSEAConfig()

    # Validate all modules present
    required_modules = set(config.module_weights.keys())
    provided_modules = set(module_scores.keys())

    if not provided_modules >= required_modules:
        missing = required_modules - provided_modules
        raise ValueError(f"Missing required modules: {missing}")

    # Validate scores in [0, 1]
    for module, score in module_scores.items():
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"Module {module} score {score} must be in [0, 1]")

    # Harmonic mean weighted (non-compensatory)
    harmonic_sum = sum(
        config.module_weights[module] / max(config.epsilon, score)
        for module, score in module_scores.items()
        if module in config.module_weights
    )

    if harmonic_sum == 0:
        return 0.0, False

    G_t = 1.0 / harmonic_sum

    # Clamp to [0, 1]
    G_t = max(0.0, min(1.0, G_t))

    # Gate check
    gate_pass = G_t >= config.min_coherence_threshold

    return G_t, gate_pass


def diagnose_bottleneck(
    module_scores: dict[str, float], config: OmegaSEAConfig | None = None
) -> tuple[str, float]:
    """
    Identify bottleneck module (lowest score).

    Args:
        module_scores: Dict mapping module name to score
        config: Optional configuration

    Returns:
        Tuple of (bottleneck_module_name, score)

    Example:
        >>> scores = {"ethics_sea": 0.95, "caos_plus": 0.60, "sr_omega": 0.90}
        >>> module, score = diagnose_bottleneck(scores)
        >>> assert module == "caos_plus" and score == 0.60
    """
    config = config or OmegaSEAConfig()

    # Find module with lowest score (weighted)
    weighted_scores = {
        module: score * config.module_weights.get(module, 1.0)
        for module, score in module_scores.items()
    }

    bottleneck_module = min(weighted_scores, key=weighted_scores.get)
    bottleneck_score = module_scores[bottleneck_module]

    return bottleneck_module, bottleneck_score


def compute_resilience(
    module_healths: list[ModuleHealth], config: OmegaSEAConfig | None = None
) -> float:
    """
    Compute system resilience (operational modules ratio).

    Args:
        module_healths: List of module health objects
        config: Optional configuration

    Returns:
        Resilience score [0, 1]
    """
    if not module_healths:
        return 0.0

    operational_count = sum(1 for m in module_healths if m.is_operational)
    total_count = len(module_healths)

    resilience = operational_count / total_count

    return resilience


__all__ = [
    "OmegaSEAConfig",
    "ModuleHealth",
    "omega_sea_coherence",
    "diagnose_bottleneck",
    "compute_resilience",
]

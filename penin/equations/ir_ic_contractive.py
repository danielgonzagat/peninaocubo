"""
PENIN-Ω Equation 6: IR→IC (Incerteza Restrita → Certa) — Contratividade
========================================================================

Implementa operador de lapidação L_ψ que reduz risco informacional.

Fórmula:
    H(L_ψ(k)) ≤ ρ · H(k),  onde 0 < ρ < 1

Onde:
- H: Entropia de risco informacional
- L_ψ: Operador de lapidação (classificadores + projeção)
- ρ: Fator de contração (deve ser < 1)
- k: Item/dado

Features:
- Classificadores de risco por categoria (idolatria, dano, privacidade)
- Barreiras de controle (CBFs)
- Refinamento iterativo até convergência
- Rejeição automática de itens não-lapidáveis

Garantia: Cada iteração REDUZ risco (contratividade).
"""

from __future__ import annotations

from dataclasses import dataclass

# Re-export from canonical implementation
from penin.math.ir_ic_contractivity import (
    RiskProfile,
    apply_Lpsi_operator,
    check_contractivity,
    compute_risk_entropy,
    iterative_refinement,
)


@dataclass
class ContractivityConfig:
    """Configuration for IR→IC contractivity."""

    rho_threshold: float = 0.95  # Must be < 1.0
    max_iterations: int = 10
    convergence_epsilon: float = 1e-3
    risk_categories: list = None

    def __post_init__(self):
        if self.rho_threshold >= 1.0:
            raise ValueError("ρ must be < 1.0 for contractivity")
        if self.risk_categories is None:
            self.risk_categories = [
                "idolatry",
                "harm",
                "privacy",
                "bias",
                "misinformation",
            ]


def ir_to_ic(
    item: dict, config: ContractivityConfig | None = None
) -> tuple[dict, RiskProfile, bool]:
    """
    Apply IR→IC lapidation operator to reduce risk.

    Args:
        item: Data/model/decision to lapidate
        config: Optional configuration

    Returns:
        Tuple of:
        - Lapidated item (reduced risk)
        - Final risk profile
        - Success flag (True if ρ < threshold)

    Raises:
        ValueError: If contractivity cannot be achieved

    Example:
        >>> item = {"content": "...", "metadata": {...}}
        >>> lapidated, risk, ok = ir_to_ic(item)
        >>> assert ok and risk.contractivity_ratio < 0.95
    """
    config = config or ContractivityConfig()

    # Iterative refinement with contractivity check
    result = iterative_refinement(
        item,
        max_iterations=config.max_iterations,
        rho_target=config.rho_threshold,
        epsilon=config.convergence_epsilon,
    )

    lapidated_item = result["lapidated_item"]
    final_risk = result["final_risk_profile"]
    converged = result["converged"]

    # Verify contractivity
    rho = (
        final_risk.contractivity_ratio
        if hasattr(final_risk, "contractivity_ratio")
        else 1.0
    )
    success = converged and rho < config.rho_threshold

    return lapidated_item, final_risk, success


__all__ = [
    "ContractivityConfig",
    "ir_to_ic",
    "RiskProfile",
    "compute_risk_entropy",
    "apply_Lpsi_operator",
    "check_contractivity",
    "iterative_refinement",
]

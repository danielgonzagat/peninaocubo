"""
DEPRECATED: penin/engine/caos_plus.py
======================================

Este módulo foi CONSOLIDADO em penin/core/caos.py

Mantido apenas para compatibilidade retroativa.
Todos os novos desenvolvimentos devem usar:

    from penin.core.caos import compute_caos_plus_exponential

Este wrapper será removido em versão futura (v2.0.0).

Migração:
---------
ANTES:
    from penin.engine.caos_plus import compute_caos_plus
    score = compute_caos_plus(C, A, O, S, kappa=20.0)

DEPOIS:
    from penin.core.caos import compute_caos_plus_exponential
    score = compute_caos_plus_exponential(C, A, O, S, kappa=20.0)

OU (para tupla com details):
    from penin.core.caos import compute_caos_plus
    score, details = compute_caos_plus(C, A, O, S, kappa=20.0)
"""

from __future__ import annotations

import warnings

# Import from canonical location
from penin.core.caos import (
    compute_caos_plus_exponential as _compute_caos_plus_exponential,
)

# Deprecation warning on module import
warnings.warn(
    "penin.engine.caos_plus is deprecated and will be removed in v2.0.0. "
    "Use penin.core.caos instead:\n"
    "  from penin.core.caos import compute_caos_plus_exponential",
    DeprecationWarning,
    stacklevel=2,
)


def compute_caos_plus(
    C: float, A: float, O: float, S: float, kappa: float = 20.0
) -> float:
    """
    DEPRECATED: Use penin.core.caos.compute_caos_plus_exponential()

    CAOS⁺ exponential formula: (1 + κ·C·A)^(O·S)

    Args:
        C: Consistência [0, 1]
        A: Autoevolução [0, 1]
        O: Incognoscível [0, 1]
        S: Silêncio [0, 1]
        kappa: Ganho base (default 20.0)

    Returns:
        CAOS⁺ score ≥ 1.0

    Migration:
        from penin.core.caos import compute_caos_plus_exponential
        score = compute_caos_plus_exponential(C, A, O, S, kappa)
    """
    warnings.warn(
        "compute_caos_plus() is deprecated. "
        "Use penin.core.caos.compute_caos_plus_exponential() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _compute_caos_plus_exponential(C, A, O, S, kappa)


# Re-export for compatibility (with deprecation warning already shown on import)
__all__ = ["compute_caos_plus"]

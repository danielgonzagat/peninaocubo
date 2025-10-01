"""
PENIN-Ω Core Module
===================

Módulo central consolidado contendo implementações canônicas de:
- CAOS⁺ (Consistência, Autoevolução, Incognoscível, Silêncio)
- Equações fundamentais (L∞, Penin, Vida/Morte, IR→IC, Lyapunov)
- Algoritmos de base (EMA, clamps, validações)

Este módulo serve como SINGLE SOURCE OF TRUTH para toda lógica matemática
e algorítmica fundamental do sistema PENIN-Ω.

Migração de código legado:
--------------------------
- penin/engine/caos_plus.py → penin/core/caos.py
- penin/omega/caos.py → penin/core/caos.py (consolidado)
- penin/equations/caos_plus.py → penin/core/caos.py (consolidado)

Uso:
----
    from penin.core.caos import compute_caos_plus_exponential, CAOSConfig
    from penin.core import __version__

    config = CAOSConfig(kappa=25.0)
    caos_score = compute_caos_plus_exponential(0.9, 0.8, 0.3, 0.85, config.kappa)
"""

from __future__ import annotations

# Version
__version__ = "1.0.0-alpha"

# Core CAOS+ module
from .caos import (
    # Enums
    CAOSComponent,
    CAOSFormula,
    # Metrics
    ConsistencyMetrics,
    AutoevolutionMetrics,
    IncognoscibleMetrics,
    SilenceMetrics,
    # Config & State
    CAOSConfig,
    CAOSState,
    # Core computation functions
    compute_caos_plus_exponential,
    phi_caos,
    compute_caos_plus_simple,
    compute_caos_plus_complete,
    # Compatibility wrappers
    compute_caos_plus,
    caos_plus,
    # Helpers
    clamp01,
    clamp,
    compute_ema_alpha,
    harmonic_mean,
    geometric_mean,
    caos_gradient,
    # Tracker
    CAOSTracker,
    # Constants
    EPS,
    DEFAULT_KAPPA,
    DEFAULT_GAMMA,
)

# Public API
__all__ = [
    # Version
    "__version__",
    # CAOS+ Enums
    "CAOSComponent",
    "CAOSFormula",
    # CAOS+ Metrics
    "ConsistencyMetrics",
    "AutoevolutionMetrics",
    "IncognoscibleMetrics",
    "SilenceMetrics",
    # CAOS+ Config & State
    "CAOSConfig",
    "CAOSState",
    # CAOS+ Core functions
    "compute_caos_plus_exponential",
    "phi_caos",
    "compute_caos_plus_simple",
    "compute_caos_plus_complete",
    # CAOS+ Compatibility
    "compute_caos_plus",
    "caos_plus",
    # CAOS+ Helpers
    "clamp01",
    "clamp",
    "compute_ema_alpha",
    "harmonic_mean",
    "geometric_mean",
    "caos_gradient",
    # CAOS+ Tracker
    "CAOSTracker",
    # Constants
    "EPS",
    "DEFAULT_KAPPA",
    "DEFAULT_GAMMA",
]

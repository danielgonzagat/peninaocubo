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
# Persistence and state management
from .artifacts import NumericVectorArtifact
from .caos import (
    DEFAULT_GAMMA,
    DEFAULT_KAPPA,
    # Constants
    EPS,
    AutoevolutionMetrics,
    # Enums
    CAOSComponent,
    CAOSComponents,
    # Config & State
    CAOSConfig,
    CAOSFormula,
    CAOSPlusEngine,
    CAOSState,
    # Tracker
    CAOSTracker,
    # Metrics
    ConsistencyMetrics,
    IncognoscibleMetrics,
    SilenceMetrics,
    caos_gradient,
    caos_plus,
    clamp,
    # Helpers
    clamp01,
    # Compatibility wrappers
    compute_caos_plus,
    compute_caos_plus_complete,
    # Core computation functions
    compute_caos_plus_exponential,
    compute_caos_plus_simple,
    compute_ema_alpha,
    geometric_mean,
    harmonic_mean,
    phi_caos,
)
from .orchestrator import OmegaMetaOrchestrator
from .serialization import StateEncoder, state_decoder

# Public API
__all__ = [
    # Version
    "__version__",
    # CAOS+ Enums
    "CAOSComponent",
    "CAOSFormula",
    "CAOSComponents",
    # CAOS+ Metrics
    "ConsistencyMetrics",
    "AutoevolutionMetrics",
    "IncognoscibleMetrics",
    "SilenceMetrics",
    # CAOS+ Config & State
    "CAOSConfig",
    "CAOSState",
    "CAOSPlusEngine",
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
    # Persistence
    "NumericVectorArtifact",
    "OmegaMetaOrchestrator",
    "StateEncoder",
    "state_decoder",
]

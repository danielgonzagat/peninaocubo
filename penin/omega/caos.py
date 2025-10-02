"""
PENIN-Ω CAOS Module - Compatibility layer for omega.caos imports
=================================================================

This module provides a compatibility layer for importing CAOS components
directly from penin.omega.caos. All actual implementations are in penin.core.caos.

Usage:
    from penin.omega import caos
    result = caos.phi_caos(0.5, 0.5, 0.5, 0.5)
    components = caos.CAOSComponents(0.5, 0.5, 0.5, 0.5)
"""

# Re-export everything from core.caos
from penin.core.caos import (
    CAOSComponent,
    CAOSComponents,
    CAOSConfig,
    CAOSFormula,
    CAOSPlusEngine,
    CAOSTracker,
    caos_plus,
    compute_caos_plus,
    compute_caos_plus_exponential,
    phi_caos,
)

# Import _clamp from life_eq for backward compatibility
from penin.omega.life_eq import _clamp

__all__ = [
    # Functions
    "phi_caos",
    "compute_caos_plus",
    "compute_caos_plus_exponential",
    "caos_plus",
    "_clamp",  # Utility function
    # Classes
    "CAOSComponents",
    "CAOSConfig",
    "CAOSPlusEngine",
    "CAOSTracker",
    # Enums
    "CAOSComponent",
    "CAOSFormula",
]

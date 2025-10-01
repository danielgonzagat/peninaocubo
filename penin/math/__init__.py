"""
PENIN-Ω Mathematical Utilities
===============================

Core mathematical functions for AGAPE, L∞, and OCI metrics.
"""

from __future__ import annotations

from .agape import agape_score
from .linf import linf_aggregate, linf_distance
from .oci import oci_score

__all__ = [
    "agape_score",
    "linf_aggregate",
    "linf_distance",
    "oci_score",
]

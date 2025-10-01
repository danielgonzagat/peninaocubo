"""
PENIN-Ω Evolution Engine
========================

Core evolution engine implementing Master Equation, CAOS+, and Fibonacci-based tuning.
"""

from __future__ import annotations

from .caos_plus import compute_caos_plus

__all__ = [
    "compute_caos_plus",
]

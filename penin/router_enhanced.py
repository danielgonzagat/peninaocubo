"""Backwards-compatible wrapper around :mod:`penin.router`.

Historically the project shipped an ``EnhancedMultiLLMRouter`` that lived in
``router_enhanced.py``. After consolidating the implementations there is a
single production-ready router in :mod:`penin.router`. This module keeps the old
import paths working while delegating everything to the unified router.
"""

from __future__ import annotations

from typing import Any, Iterable

from penin.providers.base import BaseProvider

from .router import MultiLLMRouter


class EnhancedMultiLLMRouter(MultiLLMRouter):
    """Alias maintained for guides and downstream code."""


def create_enhanced_router(
    providers: Iterable[BaseProvider], daily_budget_usd: float = 5.0, **kwargs: Any
) -> EnhancedMultiLLMRouter:
    """Factory mirroring the historic helper."""

    return EnhancedMultiLLMRouter(providers=providers, daily_budget_usd=daily_budget_usd, **kwargs)

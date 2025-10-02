"""
Cost Optimization for Multi-LLM Router
=======================================

Selects optimal provider based on cost, quality, and latency trade-offs.

Features:
- Cost-based provider ranking
- Quality-adjusted cost (cost per unit quality)
- Budget-aware selection
- Configurable optimization strategy
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class OptimizationStrategy(str, Enum):
    """Provider selection optimization strategy"""

    CHEAPEST = "cheapest"  # Pure cost minimization
    BEST_VALUE = "best_value"  # Quality-adjusted cost
    FASTEST = "fastest"  # Latency minimization
    BALANCED = "balanced"  # Balance cost, quality, latency


@dataclass
class ProviderCost:
    """Cost information for a provider"""

    provider: str
    cost_per_1k_tokens: float
    estimated_tokens: int = 1000

    @property
    def estimated_cost_usd(self) -> float:
        """Estimated cost for request in USD"""
        return (self.cost_per_1k_tokens * self.estimated_tokens) / 1000.0


@dataclass
class ProviderScore:
    """Multi-dimensional score for provider selection"""

    provider: str
    cost_score: float  # 0-1 (higher = cheaper)
    quality_score: float  # 0-1 (higher = better)
    latency_score: float  # 0-1 (higher = faster)
    availability_score: float  # 0-1 (higher = more available)

    def get_weighted_score(
        self,
        cost_weight: float = 0.4,
        quality_weight: float = 0.3,
        latency_weight: float = 0.2,
        availability_weight: float = 0.1,
    ) -> float:
        """
        Compute weighted total score.

        Args:
            cost_weight: Weight for cost (default 0.4)
            quality_weight: Weight for quality (default 0.3)
            latency_weight: Weight for latency (default 0.2)
            availability_weight: Weight for availability (default 0.1)

        Returns:
            Weighted score (0-1, higher is better)
        """
        return (
            self.cost_score * cost_weight
            + self.quality_score * quality_weight
            + self.latency_score * latency_weight
            + self.availability_score * availability_weight
        )


class CostOptimizer:
    """
    Optimizes provider selection based on cost and other factors.

    Implements multiple optimization strategies for selecting the best
    provider given cost, quality, latency, and budget constraints.
    """

    def __init__(
        self,
        strategy: OptimizationStrategy = OptimizationStrategy.BEST_VALUE,
        cost_weight: float = 0.4,
        quality_weight: float = 0.3,
        latency_weight: float = 0.2,
        availability_weight: float = 0.1,
    ):
        """
        Initialize cost optimizer.

        Args:
            strategy: Optimization strategy
            cost_weight: Weight for cost in scoring
            quality_weight: Weight for quality in scoring
            latency_weight: Weight for latency in scoring
            availability_weight: Weight for availability in scoring
        """
        self.strategy = strategy
        self.cost_weight = cost_weight
        self.quality_weight = quality_weight
        self.latency_weight = latency_weight
        self.availability_weight = availability_weight

    def select_provider(
        self,
        providers: list[str],
        provider_costs: dict[str, float],
        provider_quality: dict[str, float] | None = None,
        provider_latency: dict[str, float] | None = None,
        provider_availability: dict[str, float] | None = None,
        budget_remaining: float | None = None,
        estimated_tokens: int = 1000,
    ) -> str | None:
        """
        Select optimal provider based on strategy.

        Args:
            providers: Available providers
            provider_costs: Cost per 1k tokens for each provider
            provider_quality: Quality score (0-1) for each provider
            provider_latency: Latency (ms) for each provider
            provider_availability: Availability score (0-1) for each provider
            budget_remaining: Remaining budget in USD
            estimated_tokens: Estimated tokens for request

        Returns:
            Selected provider name or None if no suitable provider
        """
        if not providers:
            return None

        # Filter out providers without cost info
        candidates = [p for p in providers if p in provider_costs]
        if not candidates:
            return None

        # Filter by budget if specified
        if budget_remaining is not None:
            candidates = [
                p
                for p in candidates
                if self._estimate_cost(p, provider_costs, estimated_tokens)
                <= budget_remaining
            ]
            if not candidates:
                return None  # No affordable providers

        # Select based on strategy
        if self.strategy == OptimizationStrategy.CHEAPEST:
            return self._select_cheapest(candidates, provider_costs, estimated_tokens)

        elif self.strategy == OptimizationStrategy.FASTEST:
            return self._select_fastest(candidates, provider_latency or {})

        elif self.strategy == OptimizationStrategy.BEST_VALUE:
            return self._select_best_value(
                candidates,
                provider_costs,
                provider_quality or {},
                estimated_tokens,
            )

        elif self.strategy == OptimizationStrategy.BALANCED:
            return self._select_balanced(
                candidates,
                provider_costs,
                provider_quality or {},
                provider_latency or {},
                provider_availability or {},
                estimated_tokens,
            )

        return candidates[0]  # Fallback to first

    def _select_cheapest(
        self,
        candidates: list[str],
        provider_costs: dict[str, float],
        estimated_tokens: int,
    ) -> str:
        """Select cheapest provider"""
        return min(
            candidates,
            key=lambda p: self._estimate_cost(p, provider_costs, estimated_tokens),
        )

    def _select_fastest(
        self, candidates: list[str], provider_latency: dict[str, float]
    ) -> str:
        """Select fastest provider"""
        if not provider_latency:
            return candidates[0]
        return min(
            candidates, key=lambda p: provider_latency.get(p, float("inf"))
        )

    def _select_best_value(
        self,
        candidates: list[str],
        provider_costs: dict[str, float],
        provider_quality: dict[str, float],
        estimated_tokens: int,
    ) -> str:
        """Select best value (quality per dollar)"""

        def value_score(p: str) -> float:
            cost = self._estimate_cost(p, provider_costs, estimated_tokens)
            quality = provider_quality.get(p, 0.5)  # Default 0.5
            # Return quality per dollar (higher is better)
            return quality / (cost + 1e-6)

        return max(candidates, key=value_score)

    def _select_balanced(
        self,
        candidates: list[str],
        provider_costs: dict[str, float],
        provider_quality: dict[str, float],
        provider_latency: dict[str, float],
        provider_availability: dict[str, float],
        estimated_tokens: int,
    ) -> str:
        """Select provider with best balanced score"""
        # Compute scores for each candidate
        scores = {}
        for provider in candidates:
            # Normalize scores (0-1, higher is better)
            cost_score = self._normalize_cost_score(
                provider, candidates, provider_costs, estimated_tokens
            )
            quality_score = provider_quality.get(provider, 0.5)
            latency_score = self._normalize_latency_score(
                provider, candidates, provider_latency
            )
            availability_score = provider_availability.get(provider, 1.0)

            # Compute weighted score
            score = ProviderScore(
                provider=provider,
                cost_score=cost_score,
                quality_score=quality_score,
                latency_score=latency_score,
                availability_score=availability_score,
            )

            scores[provider] = score.get_weighted_score(
                self.cost_weight,
                self.quality_weight,
                self.latency_weight,
                self.availability_weight,
            )

        # Return provider with highest score
        return max(scores, key=scores.get)  # type: ignore

    def _estimate_cost(
        self, provider: str, provider_costs: dict[str, float], estimated_tokens: int
    ) -> float:
        """Estimate cost for provider"""
        cost_per_1k = provider_costs.get(provider, 0.0)
        return (cost_per_1k * estimated_tokens) / 1000.0

    def _normalize_cost_score(
        self,
        provider: str,
        candidates: list[str],
        provider_costs: dict[str, float],
        estimated_tokens: int,
    ) -> float:
        """Normalize cost to 0-1 score (higher = cheaper)"""
        costs = [
            self._estimate_cost(p, provider_costs, estimated_tokens) for p in candidates
        ]
        min_cost = min(costs)
        max_cost = max(costs)

        if max_cost == min_cost:
            return 1.0

        provider_cost = self._estimate_cost(provider, provider_costs, estimated_tokens)
        # Invert so higher score = cheaper
        return 1.0 - ((provider_cost - min_cost) / (max_cost - min_cost))

    def _normalize_latency_score(
        self,
        provider: str,
        candidates: list[str],
        provider_latency: dict[str, float],
    ) -> float:
        """Normalize latency to 0-1 score (higher = faster)"""
        latencies = [provider_latency.get(p, 100.0) for p in candidates]
        min_lat = min(latencies)
        max_lat = max(latencies)

        if max_lat == min_lat:
            return 1.0

        provider_lat = provider_latency.get(provider, 100.0)
        # Invert so higher score = faster (lower latency)
        return 1.0 - ((provider_lat - min_lat) / (max_lat - min_lat))

"""
Analytics for Multi-LLM Router
===============================

Tracks performance metrics, success rates, and latency percentiles.

Features:
- Per-provider success rate tracking
- Latency percentiles (p50, p90, p95, p99)
- Request/error counters
- Time-windowed statistics
"""

from __future__ import annotations

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RequestMetrics:
    """Metrics for a single request"""

    provider: str
    latency_ms: float
    success: bool
    timestamp: float
    cost_usd: float = 0.0
    tokens: int = 0


@dataclass
class ProviderAnalytics:
    """Analytics for a single provider"""

    provider: str
    requests_total: int = 0
    successes: int = 0
    failures: int = 0
    total_latency_ms: float = 0.0
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    latencies: deque[float] = field(default_factory=lambda: deque(maxlen=1000))

    @property
    def success_rate(self) -> float:
        """Success rate (0.0 to 1.0)"""
        if self.requests_total == 0:
            return 0.0
        return self.successes / self.requests_total

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds"""
        if self.requests_total == 0:
            return 0.0
        return self.total_latency_ms / self.requests_total

    @property
    def avg_cost_per_request(self) -> float:
        """Average cost per request (USD)"""
        if self.requests_total == 0:
            return 0.0
        return self.total_cost_usd / self.requests_total

    def get_latency_percentiles(self) -> dict[str, float]:
        """
        Calculate latency percentiles.

        Returns:
            Dict of percentile_name -> latency_ms
        """
        if not self.latencies:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}

        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)

        return {
            "p50": sorted_latencies[int(n * 0.50)] if n > 0 else 0.0,
            "p90": sorted_latencies[int(n * 0.90)] if n > 1 else 0.0,
            "p95": sorted_latencies[int(n * 0.95)] if n > 1 else 0.0,
            "p99": sorted_latencies[int(n * 0.99)] if n > 1 else 0.0,
        }


class AnalyticsTracker:
    """
    Tracks analytics for multiple providers.

    Collects performance metrics, success rates, and latency distributions.
    """

    def __init__(self, history_window: int = 1000):
        """
        Initialize analytics tracker.

        Args:
            history_window: Number of recent requests to track per provider
        """
        self.history_window = history_window
        self._providers: dict[str, ProviderAnalytics] = {}
        self._recent_requests: deque[RequestMetrics] = deque(maxlen=10000)

    def record_request(
        self,
        provider: str,
        latency_ms: float,
        success: bool,
        cost_usd: float = 0.0,
        tokens: int = 0,
    ) -> None:
        """
        Record a request for analytics.

        Args:
            provider: Provider name
            latency_ms: Request latency in milliseconds
            success: Whether request succeeded
            cost_usd: Cost of request (USD)
            tokens: Tokens used
        """
        # Get or create provider analytics
        if provider not in self._providers:
            self._providers[provider] = ProviderAnalytics(
                provider=provider,
                latencies=deque(maxlen=self.history_window),
            )

        analytics = self._providers[provider]

        # Update counters
        analytics.requests_total += 1
        if success:
            analytics.successes += 1
        else:
            analytics.failures += 1

        # Update aggregates
        analytics.total_latency_ms += latency_ms
        analytics.total_cost_usd += cost_usd
        analytics.total_tokens += tokens

        # Add to latency history
        analytics.latencies.append(latency_ms)

        # Store request
        self._recent_requests.append(
            RequestMetrics(
                provider=provider,
                latency_ms=latency_ms,
                success=success,
                timestamp=time.time(),
                cost_usd=cost_usd,
                tokens=tokens,
            )
        )

    def get_provider_analytics(self, provider: str) -> ProviderAnalytics | None:
        """
        Get analytics for a specific provider.

        Args:
            provider: Provider name

        Returns:
            Provider analytics or None if not found
        """
        return self._providers.get(provider)

    def get_all_analytics(self) -> dict[str, ProviderAnalytics]:
        """
        Get analytics for all providers.

        Returns:
            Dict of provider -> analytics
        """
        return dict(self._providers)

    def get_success_rate(self, provider: str) -> float:
        """
        Get success rate for provider.

        Args:
            provider: Provider name

        Returns:
            Success rate (0.0 to 1.0)
        """
        analytics = self._providers.get(provider)
        return analytics.success_rate if analytics else 0.0

    def get_latency_percentiles(self, provider: str) -> dict[str, float]:
        """
        Get latency percentiles for provider.

        Args:
            provider: Provider name

        Returns:
            Dict of percentile -> latency_ms
        """
        analytics = self._providers.get(provider)
        return analytics.get_latency_percentiles() if analytics else {}

    def export_metrics(self) -> dict[str, Any]:
        """
        Export Prometheus-style metrics.

        Returns:
            Dict of metric_name -> value
        """
        metrics = {}

        for provider, analytics in self._providers.items():
            prefix = f'penin_router_analytics_{{provider="{provider}"}}'

            metrics[f"{prefix}_requests_total"] = analytics.requests_total
            metrics[f"{prefix}_successes"] = analytics.successes
            metrics[f"{prefix}_failures"] = analytics.failures
            metrics[f"{prefix}_success_rate"] = analytics.success_rate
            metrics[f"{prefix}_avg_latency_ms"] = analytics.avg_latency_ms
            metrics[f"{prefix}_avg_cost_usd"] = analytics.avg_cost_per_request

            # Percentiles
            percentiles = analytics.get_latency_percentiles()
            for name, value in percentiles.items():
                metrics[f"{prefix}_latency_{name}_ms"] = value

        return metrics

    def reset(self, provider: str | None = None) -> None:
        """
        Reset analytics.

        Args:
            provider: Provider to reset (None = reset all)
        """
        if provider is None:
            self._providers.clear()
            self._recent_requests.clear()
        else:
            if provider in self._providers:
                del self._providers[provider]
            # Filter out requests for this provider
            self._recent_requests = deque(
                (req for req in self._recent_requests if req.provider != provider),
                maxlen=10000,
            )

"""
PENIN-Ω Budget Tracker
======================

Tracks daily USD budget with soft/hard limits for multi-LLM router.

Features:
- Daily budget limit (USD)
- Soft limit warning (95%)
- Hard limit enforcement (100%)
- Token consumption tracking
- Provider-level breakdown
- Reset at midnight UTC
- Metrics export for Prometheus

Usage:
    tracker = BudgetTracker(daily_limit_usd=100.0)
    
    # Track request
    if tracker.can_proceed(cost_usd=0.05):
        tracker.track_request(
            provider="openai",
            tokens=1500,
            cost_usd=0.05,
            success=True
        )
    
    # Get usage
    usage = tracker.get_usage()
    print(f"Used: ${usage['spend_today']:.2f} / ${usage['daily_limit']:.2f}")
    
    # Check if soft/hard limit reached
    if tracker.is_soft_limit_reached():
        logger.warning("Approaching daily budget limit")
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RequestRecord:
    """Single request record for audit trail"""

    timestamp: float
    provider: str
    tokens: int
    cost_usd: float
    success: bool
    endpoint: str | None = None


@dataclass
class ProviderStats:
    """Statistics per provider"""

    requests_total: int = 0
    requests_success: int = 0
    requests_failed: int = 0
    tokens_total: int = 0
    cost_total_usd: float = 0.0

    def success_rate(self) -> float:
        """Calculate success rate [0, 1]"""
        if self.requests_total == 0:
            return 0.0
        return self.requests_success / self.requests_total

    def avg_cost_per_request(self) -> float:
        """Average cost per request (USD)"""
        if self.requests_total == 0:
            return 0.0
        return self.cost_total_usd / self.requests_total


class BudgetTracker:
    """
    Tracks daily budget with soft/hard limits

    Soft limit (95%): Trigger warning, allow requests
    Hard limit (100%): Block requests, fail-closed

    Automatically resets at midnight UTC.
    """

    def __init__(
        self,
        daily_limit_usd: float = 100.0,
        soft_limit_ratio: float = 0.95,
        auto_reset: bool = True,
    ):
        """
        Initialize budget tracker

        Args:
            daily_limit_usd: Daily budget limit in USD
            soft_limit_ratio: Ratio for soft limit warning (0.95 = 95%)
            auto_reset: Automatically reset at midnight UTC
        """
        if daily_limit_usd <= 0:
            raise ValueError("daily_limit_usd must be positive")
        if not 0.0 < soft_limit_ratio < 1.0:
            raise ValueError("soft_limit_ratio must be in (0, 1)")

        self.daily_limit_usd = daily_limit_usd
        self.soft_limit_ratio = soft_limit_ratio
        self.auto_reset = auto_reset

        # Current state
        self.spend_today_usd = 0.0
        self.tokens_consumed = 0
        self.requests_count = 0

        # Provider breakdown
        self.provider_stats: dict[str, ProviderStats] = defaultdict(ProviderStats)

        # Audit trail (last 1000 requests)
        self.request_history: list[RequestRecord] = []
        self.max_history = 1000

        # Tracking
        self.last_reset_timestamp = time.time()
        self.current_day_utc = self._get_current_day_utc()

        # State flags
        self.soft_limit_triggered = False
        self.hard_limit_triggered = False

        logger.info(
            f"BudgetTracker initialized: daily_limit=${daily_limit_usd:.2f}, "
            f"soft_limit={soft_limit_ratio*100:.0f}%"
        )

    def _get_current_day_utc(self) -> int:
        """Get current day as YYYYMMDD (UTC)"""
        now_utc = datetime.now(timezone.utc)
        return int(now_utc.strftime("%Y%m%d"))

    def _check_and_reset_if_new_day(self) -> None:
        """Check if new day and reset if needed"""
        if not self.auto_reset:
            return

        current_day = self._get_current_day_utc()
        if current_day != self.current_day_utc:
            logger.info(
                f"New day detected (UTC): {self.current_day_utc} → {current_day}. "
                "Resetting budget."
            )
            self.reset()
            self.current_day_utc = current_day

    def reset(self) -> None:
        """Reset all counters (manual or automatic at midnight UTC)"""
        logger.info(
            f"Budget reset: spent ${self.spend_today_usd:.4f}, "
            f"requests={self.requests_count}, tokens={self.tokens_consumed}"
        )

        self.spend_today_usd = 0.0
        self.tokens_consumed = 0
        self.requests_count = 0
        self.provider_stats.clear()
        self.request_history.clear()
        self.last_reset_timestamp = time.time()
        self.soft_limit_triggered = False
        self.hard_limit_triggered = False

    def can_proceed(self, cost_usd: float) -> bool:
        """
        Check if request can proceed given cost

        Args:
            cost_usd: Estimated cost of request

        Returns:
            True if within hard limit, False otherwise
        """
        self._check_and_reset_if_new_day()

        projected_spend = self.spend_today_usd + cost_usd

        # Hard limit check
        if projected_spend > self.daily_limit_usd:
            if not self.hard_limit_triggered:
                logger.error(
                    f"HARD LIMIT REACHED: ${self.spend_today_usd:.2f} + ${cost_usd:.2f} "
                    f"> ${self.daily_limit_usd:.2f}. Blocking request."
                )
                self.hard_limit_triggered = True
            return False

        # Soft limit warning
        soft_limit_usd = self.daily_limit_usd * self.soft_limit_ratio
        if projected_spend > soft_limit_usd and not self.soft_limit_triggered:
            logger.warning(
                f"SOFT LIMIT REACHED: ${projected_spend:.2f} "
                f"> ${soft_limit_usd:.2f} ({self.soft_limit_ratio*100:.0f}%). "
                "Approaching daily budget limit."
            )
            self.soft_limit_triggered = True

        return True

    def track_request(
        self,
        provider: str,
        tokens: int,
        cost_usd: float,
        success: bool,
        endpoint: str | None = None,
    ) -> None:
        """
        Track a completed request

        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            tokens: Number of tokens consumed
            cost_usd: Actual cost in USD
            success: Whether request succeeded
            endpoint: Optional endpoint identifier
        """
        self._check_and_reset_if_new_day()

        # Update global counters
        self.spend_today_usd += cost_usd
        self.tokens_consumed += tokens
        self.requests_count += 1

        # Update provider stats
        stats = self.provider_stats[provider]
        stats.requests_total += 1
        if success:
            stats.requests_success += 1
        else:
            stats.requests_failed += 1
        stats.tokens_total += tokens
        stats.cost_total_usd += cost_usd

        # Add to audit trail
        record = RequestRecord(
            timestamp=time.time(),
            provider=provider,
            tokens=tokens,
            cost_usd=cost_usd,
            success=success,
            endpoint=endpoint,
        )
        self.request_history.append(record)

        # Trim history if too large
        if len(self.request_history) > self.max_history:
            self.request_history = self.request_history[-self.max_history :]

        logger.debug(
            f"Tracked request: provider={provider}, tokens={tokens}, "
            f"cost=${cost_usd:.4f}, success={success}"
        )

    def get_usage_percent(self) -> float:
        """
        Get current usage as percentage of daily limit

        Returns:
            Usage percentage [0, 100+]
        """
        self._check_and_reset_if_new_day()
        return (self.spend_today_usd / self.daily_limit_usd) * 100.0

    def get_remaining_budget(self) -> float:
        """
        Get remaining budget in USD

        Returns:
            Remaining budget (can be negative if overrun)
        """
        self._check_and_reset_if_new_day()
        return self.daily_limit_usd - self.spend_today_usd

    def is_soft_limit_reached(self) -> bool:
        """Check if soft limit reached"""
        self._check_and_reset_if_new_day()
        return self.spend_today_usd >= (self.daily_limit_usd * self.soft_limit_ratio)

    def is_hard_limit_reached(self) -> bool:
        """Check if hard limit reached"""
        self._check_and_reset_if_new_day()
        return self.spend_today_usd >= self.daily_limit_usd

    def get_usage(self) -> dict[str, Any]:
        """
        Get comprehensive usage statistics

        Returns:
            Dictionary with usage details
        """
        self._check_and_reset_if_new_day()

        return {
            "daily_limit_usd": self.daily_limit_usd,
            "spend_today_usd": self.spend_today_usd,
            "remaining_usd": self.get_remaining_budget(),
            "usage_percent": self.get_usage_percent(),
            "tokens_consumed": self.tokens_consumed,
            "requests_count": self.requests_count,
            "soft_limit_reached": self.is_soft_limit_reached(),
            "hard_limit_reached": self.is_hard_limit_reached(),
            "last_reset_timestamp": self.last_reset_timestamp,
            "current_day_utc": self.current_day_utc,
        }

    def get_provider_stats(self, provider: str | None = None) -> dict[str, Any]:
        """
        Get provider-level statistics

        Args:
            provider: Specific provider name, or None for all

        Returns:
            Dictionary with provider stats
        """
        self._check_and_reset_if_new_day()

        if provider is not None:
            stats = self.provider_stats.get(provider, ProviderStats())
            return {
                "provider": provider,
                "requests_total": stats.requests_total,
                "requests_success": stats.requests_success,
                "requests_failed": stats.requests_failed,
                "success_rate": stats.success_rate(),
                "tokens_total": stats.tokens_total,
                "cost_total_usd": stats.cost_total_usd,
                "avg_cost_per_request": stats.avg_cost_per_request(),
            }

        # All providers
        return {
            prov: {
                "requests_total": stats.requests_total,
                "requests_success": stats.requests_success,
                "requests_failed": stats.requests_failed,
                "success_rate": stats.success_rate(),
                "tokens_total": stats.tokens_total,
                "cost_total_usd": stats.cost_total_usd,
                "avg_cost_per_request": stats.avg_cost_per_request(),
            }
            for prov, stats in self.provider_stats.items()
        }

    def export_metrics(self) -> dict[str, float]:
        """
        Export metrics for Prometheus

        Returns:
            Dictionary of metric_name -> value
        """
        self._check_and_reset_if_new_day()

        usage = self.get_usage()

        metrics = {
            "penin_budget_daily_usd": self.daily_limit_usd,
            "penin_daily_spend_usd": self.spend_today_usd,
            "penin_daily_remaining_usd": usage["remaining_usd"],
            "penin_budget_usage_percent": usage["usage_percent"],
            "penin_tokens_consumed_total": float(self.tokens_consumed),
            "penin_requests_total": float(self.requests_count),
            "penin_soft_limit_reached": float(usage["soft_limit_reached"]),
            "penin_hard_limit_reached": float(usage["hard_limit_reached"]),
        }

        # Per-provider metrics
        for provider, stats in self.provider_stats.items():
            metrics[f"penin_provider_requests_total{{provider=\"{provider}\"}}"] = (
                float(stats.requests_total)
            )
            metrics[f"penin_provider_cost_usd{{provider=\"{provider}\"}}"] = (
                stats.cost_total_usd
            )
            metrics[f"penin_provider_success_rate{{provider=\"{provider}\"}}"] = (
                stats.success_rate()
            )

        return metrics

    def __repr__(self) -> str:
        """String representation"""
        usage = self.get_usage()
        return (
            f"BudgetTracker(spend=${usage['spend_today_usd']:.2f}/"
            f"${usage['daily_limit_usd']:.2f}, "
            f"{usage['usage_percent']:.1f}%, "
            f"requests={usage['requests_count']})"
        )

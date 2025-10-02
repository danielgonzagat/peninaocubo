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
from dataclasses import dataclass
from datetime import UTC, datetime
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
        Initialize budget tracker.
        
        Args:
            daily_limit_usd: Maximum daily budget in USD
            soft_limit_ratio: Ratio for soft warning (0.95 = 95%)
            auto_reset: Auto-reset daily at midnight UTC
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
    
    # ========================================================================
    # PROPERTIES (for test compatibility)
    # ========================================================================
    
    @property
    def used_usd(self) -> float:
        """Total USD spent today"""
        return self.spend_today_usd

    @property
    def remaining_usd(self) -> float:
        """Remaining budget in USD"""
        return max(0.0, self.daily_limit_usd - self.spend_today_usd)

    @property  
    def usage_pct(self) -> float:
        """Usage percentage [0, 1]"""
        if self.daily_limit_usd == 0:
            return 1.0
        return min(1.0, self.spend_today_usd / self.daily_limit_usd)
    
    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    def _get_current_day_utc(self) -> int:
        """Get current day as YYYYMMDD (UTC)"""
        now_utc = datetime.now(UTC)
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
    
    # ========================================================================
    # RECORDING METHODS
    # ========================================================================
    
    def record_request(self, provider: str, cost_usd: float, tokens_used: int, success: bool = True):
        """
        Record a request for tracking (simplified API).
        
        Args:
            provider: Provider name (e.g., "openai")
            cost_usd: Cost in USD
            tokens_used: Number of tokens consumed
            success: Whether request succeeded
        """
        self._check_and_reset_if_new_day()
        
        # Update totals
        self.spend_today_usd += cost_usd
        self.tokens_consumed += tokens_used
        self.requests_count += 1
        
        # Update provider stats
        stats = self.provider_stats[provider]
        stats.requests_total += 1
        if success:
            stats.requests_success += 1
        else:
            stats.requests_failed += 1
        stats.tokens_total += tokens_used
        stats.cost_total_usd += cost_usd
        
        # Add to history (keep last 1000)
        self.request_history.append(
            RequestRecord(
                timestamp=time.time(),
                provider=provider,
                tokens=tokens_used,
                cost_usd=cost_usd,
                success=success,
            )
        )
        if len(self.request_history) > 1000:
            self.request_history.pop(0)
        
        logger.debug(
            f"Tracked: {provider} ${cost_usd:.4f} ({tokens_used} tokens) success={success}"
        )

    def track_request(
        self,
        provider: str,
        tokens: int,
        cost_usd: float,
        success: bool,
        endpoint: str | None = None,
    ) -> None:
        """
        Track a completed request (full API).

        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            tokens: Number of tokens consumed
            cost_usd: Actual cost in USD
            success: Whether request succeeded
            endpoint: Optional endpoint identifier
        """
        self.record_request(provider, cost_usd, tokens, success)
    
    # ========================================================================
    # CHECK METHODS
    # ========================================================================
    
    def is_soft_limit_exceeded(self) -> bool:
        """Check if soft limit exceeded"""
        self._check_and_reset_if_new_day()
        return self.usage_pct >= self.soft_limit_ratio

    def is_hard_limit_exceeded(self) -> bool:
        """Check if hard limit exceeded"""
        self._check_and_reset_if_new_day()
        return self.usage_pct >= 1.0

    def can_afford_request(self, estimated_cost: float) -> bool:
        """
        Check if we can afford a request.
        
        Args:
            estimated_cost: Estimated cost in USD
        
        Returns:
            True if within budget, False otherwise
        """
        self._check_and_reset_if_new_day()
        return (self.spend_today_usd + estimated_cost) <= self.daily_limit_usd

    def get_provider_stats(self, provider: str) -> ProviderStats:
        """
        Get statistics for a provider.
        
        Args:
            provider: Provider name
        
        Returns:
            ProviderStats for that provider
        """
        return self.provider_stats[provider]
    
    def get_usage_percent(self) -> float:
        """Get current usage as percentage [0, 100+]"""
        self._check_and_reset_if_new_day()
        return (self.spend_today_usd / self.daily_limit_usd) * 100.0
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget in USD"""
        self._check_and_reset_if_new_day()
        return self.daily_limit_usd - self.spend_today_usd
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"BudgetTracker(daily_limit=${self.daily_limit_usd:.2f}, "
            f"used=${self.spend_today_usd:.2f}, "
            f"remaining=${self.remaining_usd:.2f}, "
            f"usage={self.usage_pct*100:.1f}%)"
        )

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

    def is_soft_limit_reached(self) -> bool:
        """Check if soft limit reached"""
        self._check_and_reset_if_new_day()
        return self.spend_today_usd >= (self.daily_limit_usd * self.soft_limit_ratio)

    def is_hard_limit_reached(self) -> bool:
        """Check if hard limit reached (cannot proceed)"""
        self._check_and_reset_if_new_day()
        return self.spend_today_usd >= self.daily_limit_usd

    def get_usage(self) -> dict[str, Any]:
        """
        Get current usage statistics

        Returns:
            Dict with spend_today, daily_limit, remaining, percent, etc.
        """
        self._check_and_reset_if_new_day()

        return {
            "spend_today": self.spend_today_usd,
            "daily_limit": self.daily_limit_usd,
            "remaining": max(0.0, self.daily_limit_usd - self.spend_today_usd),
            "percent": (self.spend_today_usd / self.daily_limit_usd) * 100.0,
            "tokens": self.tokens_consumed,
            "requests": self.requests_count,
            "soft_limit_reached": self.is_soft_limit_reached(),
            "hard_limit_reached": self.is_hard_limit_reached(),
        }

    def get_provider_breakdown(self) -> dict[str, dict[str, Any]]:
        """
        Get breakdown by provider

        Returns:
            Dict mapping provider → stats dict
        """
        self._check_and_reset_if_new_day()

        breakdown = {}
        for provider, stats in self.provider_stats.items():
            breakdown[provider] = {
                "requests": stats.requests_total,
                "tokens": stats.tokens_total,
                "cost_usd": stats.cost_total_usd,
                "success_rate": stats.success_rate(),
                "avg_cost": stats.avg_cost_per_request(),
            }

        return breakdown

    def export_metrics(self) -> dict[str, Any]:
        """
        Export metrics for Prometheus/monitoring in expected format.

        Returns:
            Dict with Prometheus-style metric names
        """
        self._check_and_reset_if_new_day()
        
        metrics = {
            # Budget metrics
            "penin_budget_daily_usd": self.daily_limit_usd,
            "penin_daily_spend_usd": self.spend_today_usd,
            "penin_daily_remaining_usd": self.remaining_usd,
            "penin_budget_usage_percent": self.usage_pct * 100.0,
            "penin_tokens_consumed_total": float(self.tokens_consumed),
            "penin_requests_total": float(self.requests_count),
        }
        
        # Provider-specific metrics
        for provider, stats in self.provider_stats.items():
            metrics[f'penin_provider_requests_total{{provider="{provider}"}}'] = float(stats.requests_total)
            metrics[f'penin_provider_cost_usd{{provider="{provider}"}}'] = stats.cost_total_usd
            metrics[f'penin_provider_tokens{{provider="{provider}"}}'] = float(stats.tokens_total)
            metrics[f'penin_provider_success_rate{{provider="{provider}"}}'] = stats.success_rate()
        
        return metrics


__all__ = ["BudgetTracker", "ProviderStats", "RequestRecord"]

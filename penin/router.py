import asyncio
import time
import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
# ensure single datetime import (avoid duplicates in tests)
# using datetime alias handled above
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from penin.config import settings
except Exception:
    class _FallbackSettings:
        PENIN_MAX_PARALLEL_PROVIDERS: int = 3
        PENIN_BUDGET_DAILY_USD: float = 5.0
    settings = _FallbackSettings()
from penin.providers.base import BaseProvider, LLMResponse


class CostTracker:
    """Daily cost tracker with rollover and simple persistence-less state."""
    def __init__(self, budget_usd: float = 5.0, state_path: Optional[str] = None):
        self.budget_usd = float(budget_usd)
        self.state_path = state_path
        self.state = {
            "date": date.today().isoformat(),
            "total_cost_usd": 0.0,
            "total_tokens": 0,
            "request_count": 0,
        }

    def _check_date_rollover(self):
        today = date.today().isoformat()
        if self.state["date"] != today:
            self.state["date"] = today
            self.state["total_cost_usd"] = 0.0
            self.state["total_tokens"] = 0
            self.state["request_count"] = 0

    def record(self, provider: str, cost_usd: float, tokens: int = 0):
        self._check_date_rollover()
        self.state["total_cost_usd"] += float(cost_usd)
        self.state["total_tokens"] += int(tokens)
        self.state["request_count"] += 1

    def is_over_budget(self) -> bool:
        self._check_date_rollover()
        return self.state["total_cost_usd"] >= self.budget_usd

    def remaining_budget(self) -> float:
        self._check_date_rollover()
        remain = self.budget_usd - self.state["total_cost_usd"]
        return max(0.0, float(remain))


class MultiLLMRouter:
    """
    Multi-LLM router with cost-aware selection and budget tracking.
    
    P0-4: Includes cost/budget in scoring to prevent overspending.
    """
    
    def __init__(
        self,
        providers: List[BaseProvider],
        daily_budget_usd: Optional[float] = None,
        cost_weight: float = 0.3,
        latency_weight: float = 0.3,
        quality_weight: float = 0.4,
        **kwargs,
    ):
        self.providers = providers[: settings.PENIN_MAX_PARALLEL_PROVIDERS]
        # Support alias budget_usd from tests
        alias_budget = kwargs.get("budget_usd")
        self.daily_budget_usd = (
            alias_budget if alias_budget is not None else (daily_budget_usd or settings.PENIN_BUDGET_DAILY_USD)
        )
        self.cost_weight = cost_weight
        self.latency_weight = latency_weight
        self.quality_weight = quality_weight
        
        # P0-4: Budget tracking
        self._daily_spend = 0.0
        self._last_reset = datetime.now().date()
        self._total_tokens = 0
        self._request_count = 0
    
    def _reset_daily_budget_if_needed(self):
        """Reset daily budget tracker at midnight"""
        today = datetime.now().date()
        if today > self._last_reset:
            self._daily_spend = 0.0
            self._total_tokens = 0
            self._request_count = 0
            self._last_reset = today
    
    def _get_today_usage(self) -> float:
        """Get today's total usage in USD"""
        self._reset_daily_budget_if_needed()
        return self._daily_spend
    
    def _add_usage(self, cost_usd: float, tokens: int = 0):
        """Add usage for today"""
        self._reset_daily_budget_if_needed()
        self._daily_spend += cost_usd
        self._total_tokens += tokens
        self._request_count += 1
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        self._reset_daily_budget_if_needed()
        return {
            "daily_spend_usd": self._daily_spend,
            "budget_remaining_usd": max(0, self.daily_budget_usd - self._daily_spend),
            "budget_used_pct": (self._daily_spend / self.daily_budget_usd) * 100,
            "total_tokens": self._total_tokens,
            "request_count": self._request_count,
            "avg_cost_per_request": self._daily_spend / max(1, self._request_count),
        }
    
    def _score(self, r: LLMResponse) -> float:
        """Score response considering content, latency, and cost"""
        # Base score for having content
        base = 1.0 if r.content else 0.0
        
        # Latency component (higher is better for lower latency)
        lat = max(0.01, r.latency_s)
        # P0 Fix: Include cost in scoring (higher cost = lower score)
        cost_scaling = getattr(self, 'cost_scaling_factor', 1000)  # Make configurable
        cost_penalty = r.cost_usd * cost_scaling
        return base + (1.0 / lat) - cost_penalty

    async def ask(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        force_budget_override: bool = False,
    ) -> LLMResponse:
        # Check budget before making requests
        current_usage = self._get_today_usage()
        if not force_budget_override and current_usage >= self.daily_budget_usd:
            raise RuntimeError(f"Daily budget exceeded: ${current_usage:.2f} >= ${self.daily_budget_usd:.2f}")
        
        tasks = [
            p.chat(messages, tools=tools, system=system, temperature=temperature)
            for p in self.providers
        ]
        results: List[LLMResponse] = await asyncio.gather(*tasks, return_exceptions=True)
        ok = [r for r in results if isinstance(r, LLMResponse)]
        if not ok:
            errors = [str(r) for r in results if isinstance(r, Exception)]
            raise RuntimeError(f"All providers failed. Errors: {errors}")

        # Select best response
        best_response = max(ok, key=self._score)

        # Record usage for all successful providers
        total_cost = sum(getattr(r, "cost_usd", 0.0) or 0.0 for r in ok)
        total_tokens = sum(
            int((getattr(r, "tokens_in", 0) or 0) + (getattr(r, "tokens_out", 0) or 0))
            for r in ok
        )
        if total_cost > 0 or total_tokens > 0:
            self._add_usage(total_cost, total_tokens)

        return best_response
        
    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        current_usage = self._get_today_usage()
        remaining = max(0.0, self.daily_budget_usd - current_usage)
        
        return {
            "daily_budget_usd": self.daily_budget_usd,
            "current_usage_usd": current_usage,
            "remaining_usd": remaining,
            "usage_percentage": (current_usage / self.daily_budget_usd) * 100,
            "budget_exceeded": current_usage >= self.daily_budget_usd,
            "date": date.today().isoformat()
        }
        
    def reset_daily_budget(self, new_budget: Optional[float] = None):
        """Reset daily budget counters (for new day or manual reset)"""
        if new_budget is not None:
            self.daily_budget_usd = float(new_budget)
        self._daily_spend = 0.0
        self._total_tokens = 0
        self._request_count = 0
        self._last_reset = datetime.now().date()

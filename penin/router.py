import asyncio
import time
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential

from penin.config import settings
from penin.providers.base import BaseProvider, LLMResponse


class CostTracker:
    """Track costs with daily budget limits"""

    def __init__(self, daily_budget: float):
        self.daily_budget = daily_budget
        self.daily_spent = 0.0
        self.reset_time = time.time()

    def add_cost(self, cost: float):
        """Add cost and reset daily counter if needed"""
        current_time = time.time()
        if current_time - self.reset_time > DAY_SECONDS:  # 24 hours
            self.daily_spent = 0.0
            self.reset_time = current_time
        self.daily_spent += cost

    def is_over_budget(self) -> bool:
        """Check if over daily budget"""
        return self.daily_spent >= self.daily_budget

    def remaining_budget(self) -> float:
        """Get remaining budget for today"""
        return max(0, self.daily_budget - self.daily_spent)


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
    ):
        self.providers = providers[: settings.PENIN_MAX_PARALLEL_PROVIDERS]
        self.daily_budget_usd = daily_budget_usd or settings.PENIN_BUDGET_DAILY_USD
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
    
    def _score(self, r: LLMResponse) -> float:
        """
        Score response considering quality, latency, and cost.
        
        P0-4: Multi-factor scoring with budget awareness.
        Lower cost is better (normalized).
        """
        # Quality: presence of content (binary for now)
        quality = 1.0 if r.content else 0.0
        
        # Latency: inverse latency (faster is better)
        lat = max(0.01, r.latency_s)
        latency_score = 1.0 / lat
        # Normalize to [0,1] assuming max 10s latency
        latency_score = min(1.0, latency_score / (1.0 / 0.1))
        
        # Cost: lower is better
        # Normalize assuming max $0.10 per request
        cost_score = max(0.0, 1.0 - (r.cost_usd / 0.10))
        
        # Weighted combination
        score = (
            self.quality_weight * quality
            + self.latency_weight * latency_score
            + self.cost_weight * cost_score
        )
        
        return score
    
    def _check_budget(self, estimated_cost: float = 0.01) -> bool:
        """
        Check if we have budget remaining for this request.
        
        P0-4: Fail-closed budget enforcement.
        """
        self._reset_daily_budget_if_needed()
        return (self._daily_spend + estimated_cost) <= self.daily_budget_usd
    
    def _record_spend(self, response: LLMResponse):
        """Record spending from response"""
        self._daily_spend += response.cost_usd
        self._total_tokens += response.tokens_in + response.tokens_out
        self._request_count += 1

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5))
    async def ask(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Ask question to multiple providers and return best response.
        
        P0-4: Includes budget checking and cost-aware selection.
        """
        # P0-4: Check budget before making requests
        if not self._check_budget():
            raise RuntimeError(
                f"Daily budget exceeded: ${self._daily_spend:.4f} / ${self.daily_budget_usd:.2f}"
            )
        
        tasks = [
            p.chat(messages, tools=tools, system=system, temperature=temperature)
            for p in self.providers
        ]
        results: List[LLMResponse] = await asyncio.gather(*tasks, return_exceptions=True)
        ok = [r for r in results if isinstance(r, LLMResponse)]
        if not ok:
            errors = [str(r) for r in results if isinstance(r, Exception)]
            raise RuntimeError(f"All providers failed. Errors: {errors}")
        
        # P0-4: Select best response with cost-aware scoring
        best = max(ok, key=self._score)
        
        # P0-4: Record actual spend
        self._record_spend(best)
        
        # P0-4: Hard-stop if budget exceeded
        if self._daily_spend > self.daily_budget_usd:
            raise RuntimeError(
                f"Budget hard-stop triggered: ${self._daily_spend:.4f} exceeds ${self.daily_budget_usd:.2f}"
            )
        
        return best
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        self._reset_daily_budget_if_needed()
        return {
            "daily_spend_usd": self._daily_spend,
            "daily_budget_usd": self.daily_budget_usd,
            "budget_remaining_usd": self.daily_budget_usd - self._daily_spend,
            "budget_used_pct": (self._daily_spend / self.daily_budget_usd) * 100,
            "total_tokens": self._total_tokens,
            "request_count": self._request_count,
            "avg_cost_per_request": self._daily_spend / max(1, self._request_count),
            "last_reset": self._last_reset.isoformat(),
        }

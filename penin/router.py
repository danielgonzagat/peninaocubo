import asyncio
import time
from typing import List, Optional, Dict, Any
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
        if current_time - self.reset_time > 86400:  # 24 hours
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
    def __init__(self, providers: List[BaseProvider], budget_usd: Optional[float] = None):
        self.providers = providers[: settings.PENIN_MAX_PARALLEL_PROVIDERS]
        # Use CostTracker for better budget management
        daily_budget = budget_usd or getattr(settings, 'PENIN_BUDGET_DAILY_USD', 100.0)
        self.cost_tracker = CostTracker(daily_budget)

    def _score(self, r: LLMResponse) -> float:
        """
        P0 FIX: Score response considering content, latency, and cost.
        Higher score is better.
        
        Score = quality + speed - normalized_cost
        """
        # Base score for having content
        base = 1.0 if r.content else 0.0
        
        # Latency penalty (lower latency = higher score)
        lat = max(0.01, r.latency_s)
        latency_score = 1.0 / lat
        
        # Cost penalty (lower cost = higher score)
        # Normalize cost to [0,1] range assuming max cost of $0.10 per call
        max_cost = getattr(settings, 'MAX_COST_PER_CALL', 0.10)
        cost = getattr(r, 'cost_usd', 0.0)
        cost_penalty = max(0.0, 1.0 - (cost / max_cost)) if max_cost > 0 else 1.0
        
        # Token usage efficiency (if available)
        token_efficiency = 1.0
        if hasattr(r, 'usage') and r.usage:
            total_tokens = r.usage.get('total_tokens', 0)
            if total_tokens > 0:
                # Prefer responses with fewer tokens (more concise)
                max_tokens = getattr(settings, 'MAX_TOKENS_EXPECTED', 4096)
                token_efficiency = max(0.1, 1.0 - (total_tokens / max_tokens))
        
        # Combined score with weights
        w_content = getattr(settings, 'ROUTER_WEIGHT_CONTENT', 0.4)
        w_latency = getattr(settings, 'ROUTER_WEIGHT_LATENCY', 0.2)
        w_cost = getattr(settings, 'ROUTER_WEIGHT_COST', 0.3)
        w_tokens = getattr(settings, 'ROUTER_WEIGHT_TOKENS', 0.1)
        
        # Normalize weights
        w_sum = w_content + w_latency + w_cost + w_tokens
        if w_sum > 0:
            w_content /= w_sum
            w_latency /= w_sum
            w_cost /= w_sum
            w_tokens /= w_sum
        
        score = (
            w_content * base +
            w_latency * latency_score +
            w_cost * cost_penalty +
            w_tokens * token_efficiency
        )
        
        # Apply budget penalty if over budget
        if self.cost_tracker.is_over_budget():
            score *= 0.01  # Heavily penalize if over budget
        
        return score

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5))
    async def ask(
        self,
        messages: List[Dict[str, Any]],
        system: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
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
        best = max(ok, key=self._score)
        
        # Track spending
        if hasattr(best, 'cost_usd'):
            self.cost_tracker.add_cost(best.cost_usd)
        
        return best
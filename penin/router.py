import asyncio
import time
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential

from penin.config import settings
from penin.providers.base import BaseProvider, LLMResponse


class MultiLLMRouter:
    def __init__(self, providers: List[BaseProvider], 
                 daily_budget_usd: float = 100.0,
                 cost_weight: float = 0.3):
        self.providers = providers[: settings.PENIN_MAX_PARALLEL_PROVIDERS]
        self.daily_budget_usd = daily_budget_usd
        self.cost_weight = cost_weight
        self.usage_file = Path.home() / ".penin_omega" / "router_usage.json"
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load today's usage
        self.daily_usage = self._load_daily_usage()

    def _load_daily_usage(self) -> Dict[str, float]:
        """Load today's usage from file"""
        today = date.today().isoformat()
        
        if not self.usage_file.exists():
            return {today: 0.0}
            
        try:
            with open(self.usage_file, 'r') as f:
                all_usage = json.load(f)
            return {today: all_usage.get(today, 0.0)}
        except Exception:
            return {today: 0.0}
            
    def _save_daily_usage(self):
        """Save usage to file"""
        try:
            # Load existing data
            all_usage = {}
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    all_usage = json.load(f)
                    
            # Update with current usage
            all_usage.update(self.daily_usage)
            
            # Keep only last 30 days
            cutoff = (datetime.now().date() - timedelta(days=30)).isoformat()
            all_usage = {k: v for k, v in all_usage.items() if k >= cutoff}
            
            # Save
            with open(self.usage_file, 'w') as f:
                json.dump(all_usage, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save usage data: {e}")
            
    def _get_today_usage(self) -> float:
        """Get today's total usage in USD"""
        today = date.today().isoformat()
        return self.daily_usage.get(today, 0.0)
        
    def _add_usage(self, cost_usd: float):
        """Add usage for today"""
        today = date.today().isoformat()
        self.daily_usage[today] = self.daily_usage.get(today, 0.0) + cost_usd
        self._save_daily_usage()
        
    def _check_budget(self, estimated_cost: float) -> bool:
        """Check if request fits within daily budget"""
        current_usage = self._get_today_usage()
        return (current_usage + estimated_cost) <= self.daily_budget_usd

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
        """Score response considering content, latency, and cost"""
        # Base score for having content
        base = 1.0 if r.content else 0.0
        
        # Latency component (higher is better for lower latency)
        lat = max(0.01, r.latency_s)
        latency_score = 1.0 / lat
        
        # Cost component (lower cost is better)
        # Normalize cost to [0,1] range, assuming max $1 per request
        cost_normalized = min(1.0, max(0.0, getattr(r, 'cost_usd', 0.0)))
        cost_score = 1.0 - cost_normalized  # Invert so lower cost = higher score
        
        # Budget penalty - heavily penalize if over budget
        budget_penalty = 1.0
        if hasattr(r, 'cost_usd') and r.cost_usd > 0:
            if not self._check_budget(r.cost_usd):
                budget_penalty = 0.1  # Severe penalty for budget violation
                
        # Combined score
        content_weight = 0.4
        latency_weight = 1.0 - self.cost_weight - content_weight
        
        score = (content_weight * base + 
                latency_weight * latency_score + 
                self.cost_weight * cost_score) * budget_penalty
                
        return score

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5))
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
        
        # Record usage
        if hasattr(best_response, 'cost_usd') and best_response.cost_usd > 0:
            self._add_usage(best_response.cost_usd)
            
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
        """Reset daily budget (for new day or manual reset)"""
        if new_budget is not None:
            self.daily_budget_usd = new_budget
            
        today = date.today().isoformat()
        self.daily_usage = {today: 0.0}
        self._save_daily_usage()

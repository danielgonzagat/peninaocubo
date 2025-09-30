import asyncio
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from penin.config import settings
from penin.providers.base import BaseProvider, LLMResponse


class MultiLLMRouter:
    """
    Multi-LLM router with cost-aware selection and in-memory daily budget tracking.
    
    - Scores provider responses by latency and cost (lower cost preferred).
    - Tracks spend, tokens, and request count for the current day.
    - Enforces a fail-closed budget cap (raises RuntimeError when exceeded).
    """

    def __init__(
        self,
        providers: List[BaseProvider],
        daily_budget_usd: Optional[float] = None,
        cost_weight: float = 0.3,
        latency_weight: float = 0.3,
        quality_weight: float = 0.4,
        cost_scaling_factor: float = 1000.0,
        # Backwards-compat alias used by some tests
        budget_usd: Optional[float] = None,
        min_request_cost_usd: float = 0.01,
    ) -> None:
        self.providers = providers[: settings.PENIN_MAX_PARALLEL_PROVIDERS]
        self.daily_budget_usd = (
            daily_budget_usd if daily_budget_usd is not None else (
                budget_usd if budget_usd is not None else settings.PENIN_BUDGET_DAILY_USD
            )
        )
        self.cost_weight = cost_weight
        self.latency_weight = latency_weight
        self.quality_weight = quality_weight
        self.cost_scaling_factor = cost_scaling_factor
        self.min_request_cost_usd = float(min_request_cost_usd)

        # Daily usage tracking (resets on date change)
        self._daily_spend: float = 0.0
        self._total_tokens: int = 0
        self._request_count: int = 0
        self._last_reset: date = datetime.now().date()

    def _reset_daily_budget_if_needed(self) -> None:
        today = datetime.now().date()
        if today > self._last_reset:
            self._daily_spend = 0.0
            self._total_tokens = 0
            self._request_count = 0
            self._last_reset = today

    def _score(self, r: LLMResponse) -> float:
        # Simple heuristic: favor content, lower latency, and lower cost
        base = 1.0 if getattr(r, "content", None) else 0.0
        lat = max(0.01, float(getattr(r, "latency_s", 0.0)))
        cost = float(getattr(r, "cost_usd", 0.0))
        return base + (1.0 / lat) - (cost * self.cost_scaling_factor)

    def get_usage_stats(self) -> Dict[str, Any]:
        self._reset_daily_budget_if_needed()
        remaining = max(0.0, float(self.daily_budget_usd) - float(self._daily_spend))
        return {
            "daily_spend_usd": float(self._daily_spend),
            "budget_remaining_usd": float(remaining),
            "daily_budget_usd": float(self.daily_budget_usd),
            "request_count": int(self._request_count),
            "total_tokens": int(self._total_tokens),
            "date": datetime.now().date().isoformat(),
            "budget_used_pct": (float(self._daily_spend) / float(self.daily_budget_usd) * 100.0)
            if float(self.daily_budget_usd) > 0 else 0.0,
        }

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5))
    async def ask(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        force_budget_override: bool = False,
    ) -> LLMResponse:
        self._reset_daily_budget_if_needed()
        if not force_budget_override and float(self._daily_spend) >= float(self.daily_budget_usd):
            raise RuntimeError(
                f"Daily budget exceeded: ${self._daily_spend:.2f} >= ${float(self.daily_budget_usd):.2f}"
            )
        # Conservative preflight check: ensure remaining budget covers at least a minimal request cost
        remaining = float(self.daily_budget_usd) - float(self._daily_spend)
        if not force_budget_override and remaining < self.min_request_cost_usd:
            raise RuntimeError(
                f"Daily budget would be exceeded by next request: remaining ${remaining:.3f} < min_request_cost ${self.min_request_cost_usd:.3f}"
            )

        tasks = [
            p.chat(messages, tools=tools, system=system, temperature=temperature)
            for p in self.providers
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        ok: List[LLMResponse] = [r for r in results if isinstance(r, LLMResponse)]
        if not ok:
            errors = [str(r) for r in results if isinstance(r, Exception)]
            raise RuntimeError(f"All providers failed. Errors: {errors}")

        best_response = max(ok, key=self._score)

        # Record spend and tokens
        cost_usd = float(getattr(best_response, "cost_usd", 0.0) or 0.0)
        self._daily_spend += cost_usd
        tokens = 0
        if hasattr(best_response, "tokens_in") or hasattr(best_response, "tokens_out"):
            tokens = int(getattr(best_response, "tokens_in", 0) or 0) + int(getattr(best_response, "tokens_out", 0) or 0)
        elif hasattr(best_response, "total_tokens"):
            tokens = int(getattr(best_response, "total_tokens", 0) or 0)
        self._total_tokens += tokens
        self._request_count += 1

        return best_response

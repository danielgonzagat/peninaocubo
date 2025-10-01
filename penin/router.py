"""Production-ready multi-LLM router with budgeting and provider analytics."""

from __future__ import annotations

import asyncio
import json
import time
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from penin.config import settings
from penin.providers.base import BaseProvider, LLMResponse


class ProviderHealth(str, Enum):
    """Health status used by the circuit breaker and analytics."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class BudgetTracker:
    """Track day-based budget consumption with automatic reset."""

    daily_budget_usd: float
    current_spend_usd: float = 0.0
    total_tokens: int = 0
    request_count: int = 0
    last_reset: date = field(default_factory=date.today)
    spend_history: deque = field(default_factory=lambda: deque(maxlen=30))

    def _reset_if_needed(self) -> None:
        today = date.today()
        if today > self.last_reset:
            self.spend_history.append(
                {
                    "date": self.last_reset.isoformat(),
                    "spend_usd": round(self.current_spend_usd, 6),
                    "tokens": self.total_tokens,
                    "requests": self.request_count,
                }
            )
            self.current_spend_usd = 0.0
            self.total_tokens = 0
            self.request_count = 0
            self.last_reset = today

    def add_usage(self, cost_usd: float, tokens: int) -> None:
        self._reset_if_needed()
        self.current_spend_usd += float(cost_usd)
        self.total_tokens += int(tokens)
        self.request_count += 1

    def remaining_budget(self) -> float:
        self._reset_if_needed()
        return max(0.0, self.daily_budget_usd - self.current_spend_usd)

    def is_budget_exceeded(self) -> bool:
        self._reset_if_needed()
        return self.current_spend_usd >= self.daily_budget_usd

    def snapshot(self) -> dict[str, Any]:
        self._reset_if_needed()
        budget_remaining = self.remaining_budget()
        usage_pct = 0.0 if self.daily_budget_usd == 0 else (self.current_spend_usd / self.daily_budget_usd) * 100
        return {
            "daily_budget_usd": self.daily_budget_usd,
            "daily_spend_usd": round(self.current_spend_usd, 6),
            "budget_remaining_usd": round(budget_remaining, 6),
            "budget_used_pct": usage_pct,
            "total_tokens": self.total_tokens,
            "request_count": self.request_count,
            "last_reset": self.last_reset.isoformat(),
            "history": list(self.spend_history),
            "budget_exceeded": self.is_budget_exceeded(),
        }

    def reset(self, new_budget_usd: float | None = None) -> None:
        if new_budget_usd is not None:
            self.daily_budget_usd = float(new_budget_usd)
        self.current_spend_usd = 0.0
        self.total_tokens = 0
        self.request_count = 0
        self.last_reset = date.today()
        self.spend_history.clear()


@dataclass
class ProviderStats:
    """Operational metrics collected for each provider call."""

    provider_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost_usd: float = 0.0
    total_latency_s: float = 0.0
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    consecutive_failures: int = 0
    last_error: str | None = None
    last_success_at: float | None = None
    last_failure_at: float | None = None
    health: ProviderHealth = ProviderHealth.HEALTHY

    def record_success(self, response: LLMResponse, latency_s: float) -> None:
        self.total_requests += 1
        self.successful_requests += 1
        self.total_cost_usd += float(getattr(response, "cost_usd", 0.0) or 0.0)
        tokens_in = int(getattr(response, "tokens_in", 0) or 0)
        tokens_out = int(getattr(response, "tokens_out", 0) or 0)
        self.total_tokens_in += tokens_in
        self.total_tokens_out += tokens_out
        self.total_latency_s += latency_s
        self.consecutive_failures = 0
        self.last_error = None
        self.last_success_at = time.time()
        self.health = ProviderHealth.HEALTHY if self.success_rate() >= 0.9 else ProviderHealth.DEGRADED

    def record_failure(self, error: Exception) -> None:
        self.total_requests += 1
        self.failed_requests += 1
        self.consecutive_failures += 1
        self.last_error = str(error)
        self.last_failure_at = time.time()
        if self.consecutive_failures >= 5:
            self.health = ProviderHealth.CIRCUIT_OPEN
        elif self.consecutive_failures >= 3:
            self.health = ProviderHealth.UNHEALTHY
        else:
            self.health = ProviderHealth.DEGRADED

    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    def avg_latency(self) -> float:
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency_s / self.successful_requests

    def total_tokens(self) -> int:
        return self.total_tokens_in + self.total_tokens_out

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": self.success_rate(),
            "total_cost_usd": round(self.total_cost_usd, 6),
            "avg_latency_s": self.avg_latency(),
            "total_tokens_in": self.total_tokens_in,
            "total_tokens_out": self.total_tokens_out,
            "total_tokens": self.total_tokens(),
            "consecutive_failures": self.consecutive_failures,
            "health": self.health.value,
            "last_error": self.last_error,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
        }


class CircuitBreaker:
    """Simple circuit breaker to avoid hammering unhealthy providers."""

    def __init__(self, failure_threshold: int = 3, recovery_timeout_s: float = 60.0, half_open_max_calls: int = 1):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_s = recovery_timeout_s
        self.half_open_max_calls = half_open_max_calls
        self._state = ProviderHealth.HEALTHY
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._half_open_calls = 0

    def can_call(self) -> bool:
        if self._state in (ProviderHealth.HEALTHY, ProviderHealth.DEGRADED):
            return True

        now = time.monotonic()
        if self._state == ProviderHealth.CIRCUIT_OPEN:
            if now - self._last_failure_time >= self.recovery_timeout_s:
                self._state = ProviderHealth.DEGRADED
                self._half_open_calls = 0
                return True
            return False

        if self._state == ProviderHealth.UNHEALTHY:
            return True

        if self._state == ProviderHealth.DEGRADED and self._half_open_calls < self.half_open_max_calls:
            self._half_open_calls += 1
            return True

        return False

    def record_success(self) -> None:
        self._state = ProviderHealth.HEALTHY
        self._failure_count = 0
        self._half_open_calls = 0

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.failure_threshold:
            self._state = ProviderHealth.CIRCUIT_OPEN
        else:
            self._state = ProviderHealth.DEGRADED

    @property
    def state(self) -> ProviderHealth:
        return self._state


def _provider_identifier(provider: BaseProvider, suffix: int) -> str:
    base = getattr(provider, "name", provider.__class__.__name__).lower()
    return f"{base}-{suffix}" if suffix else base


class MultiLLMRouter:
    """Coordinate multiple LLM providers with budget awareness and analytics."""

    def __init__(
        self,
        providers: Iterable[BaseProvider],
        daily_budget_usd: float | None = None,
        cost_weight: float = 0.3,
        latency_weight: float = 0.3,
        quality_weight: float = 0.4,
        enable_circuit_breaker: bool = True,
        state_path: Path | None = None,
    ) -> None:
        provider_list = list(providers)
        max_parallel = max(1, int(getattr(settings, "PENIN_MAX_PARALLEL_PROVIDERS", len(provider_list) or 1)))
        self.providers: list[BaseProvider] = provider_list[:max_parallel]
        self.cost_weight = cost_weight
        self.latency_weight = latency_weight
        self.quality_weight = quality_weight
        self.enable_circuit_breaker = enable_circuit_breaker
        self._state_path = state_path or Path.home() / ".penin_router_state.json"

        daily_budget = daily_budget_usd if daily_budget_usd is not None else settings.PENIN_BUDGET_DAILY_USD
        self._budget = BudgetTracker(daily_budget_usd=float(daily_budget))
        self._budget_lock = asyncio.Lock()

        self._provider_ids: dict[int, str] = {}
        self.provider_stats: dict[str, ProviderStats] = {}
        self._provider_locks: dict[str, asyncio.Lock] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}

        seen: dict[str, int] = {}
        for _idx, provider in enumerate(self.providers):
            base = getattr(provider, "name", provider.__class__.__name__).lower()
            suffix = seen.get(base, 0)
            provider_id = _provider_identifier(provider, suffix)
            seen[base] = suffix + 1
            self._provider_ids[id(provider)] = provider_id
            if not getattr(provider, "provider_id", None):
                provider.provider_id = provider_id
            self.provider_stats[provider_id] = ProviderStats(provider_id=provider_id)
            self._provider_locks[provider_id] = asyncio.Lock()
            if enable_circuit_breaker:
                self.circuit_breakers[provider_id] = CircuitBreaker()

        self._persistence_lock = asyncio.Lock()
        self._load_state()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_state(self) -> None:
        try:
            if not self._state_path.exists():
                return
            data = json.loads(self._state_path.read_text())
        except Exception:
            return

        budget = data.get("budget", {})
        if budget:
            self._budget.current_spend_usd = float(budget.get("daily_spend_usd", 0.0))
            self._budget.total_tokens = int(budget.get("total_tokens", 0))
            self._budget.request_count = int(budget.get("request_count", 0))
            last_reset = budget.get("last_reset")
            if last_reset:
                try:
                    self._budget.last_reset = date.fromisoformat(last_reset)
                except ValueError:
                    pass
            history = budget.get("history", [])
            self._budget.spend_history.extend(history)

        for pid, stats_payload in data.get("providers", {}).items():
            if pid in self.provider_stats:
                stats = self.provider_stats[pid]
                stats.total_requests = int(stats_payload.get("total_requests", stats.total_requests))
                stats.successful_requests = int(stats_payload.get("successful_requests", stats.successful_requests))
                stats.failed_requests = int(stats_payload.get("failed_requests", stats.failed_requests))
                stats.total_cost_usd = float(stats_payload.get("total_cost_usd", stats.total_cost_usd))
                stats.total_tokens_in = int(stats_payload.get("total_tokens_in", stats.total_tokens_in))
                stats.total_tokens_out = int(stats_payload.get("total_tokens_out", stats.total_tokens_out))
                stats.total_latency_s = float(stats_payload.get("avg_latency_s", 0.0)) * max(
                    1, stats.successful_requests
                )
                stats.consecutive_failures = int(stats_payload.get("consecutive_failures", stats.consecutive_failures))
                last_error = stats_payload.get("last_error")
                if last_error:
                    stats.last_error = last_error

    async def _persist_state(self) -> None:
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "budget": self._budget.snapshot(),
            "providers": {pid: stats.to_dict() for pid, stats in self.provider_stats.items()},
        }
        try:
            async with self._persistence_lock:
                self._state_path.parent.mkdir(parents=True, exist_ok=True)
                self._state_path.write_text(json.dumps(payload, indent=2))
        except Exception:
            # Persistence should never break routing; swallow errors silently.
            return

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------
    def _provider_id(self, provider: BaseProvider) -> str:
        return self._provider_ids[id(provider)]

    def _score_response(self, response: LLMResponse, stats: ProviderStats) -> float:
        has_content = 1.0 if getattr(response, "content", None) else 0.0
        latency = getattr(response, "latency_s", None) or stats.avg_latency() or 1.0
        latency_score = 1.0 / (1.0 + latency)
        cost = float(getattr(response, "cost_usd", 0.0) or 0.0)
        cost_score = 1.0 / (1.0 + cost * 100)
        quality_score = stats.success_rate()
        return (
            has_content * 0.2
            + latency_score * self.latency_weight
            + cost_score * self.cost_weight
            + quality_score * self.quality_weight
        )

    async def _invoke_provider(
        self,
        provider: BaseProvider,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None,
        system: str | None,
        temperature: float,
    ) -> tuple[LLMResponse, str]:
        provider_id = self._provider_id(provider)
        breaker = self.circuit_breakers.get(provider_id)
        if breaker and not breaker.can_call():
            raise RuntimeError(f"Circuit breaker open for provider '{provider_id}'")

        start = time.monotonic()
        try:
            response = await provider.chat(messages, tools=tools, system=system, temperature=temperature)
        except Exception as exc:  # pragma: no cover - behavior validated in tests
            async with self._provider_locks[provider_id]:
                self.provider_stats[provider_id].record_failure(exc)
                if breaker:
                    breaker.record_failure()
            raise

        latency = time.monotonic() - start
        if getattr(response, "latency_s", 0) in (0, None):
            response.latency_s = latency
        if not getattr(response, "provider", None):
            response.provider = provider_id

        async with self._provider_locks[provider_id]:
            stats = self.provider_stats[provider_id]
            stats.record_success(response, latency)
            if breaker:
                breaker.record_success()
        return response, provider_id

    def _aggregate_usage(self, responses: Iterable[LLMResponse]) -> tuple[float, int]:
        total_cost = 0.0
        total_tokens = 0
        for response in responses:
            total_cost += float(getattr(response, "cost_usd", 0.0) or 0.0)
            tokens_in = int(getattr(response, "tokens_in", 0) or 0)
            tokens_out = int(getattr(response, "tokens_out", 0) or 0)
            total_tokens += tokens_in + tokens_out
        return total_cost, total_tokens

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5))
    async def ask(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        force_budget_override: bool = False,
    ) -> LLMResponse:
        async with self._budget_lock:
            if not force_budget_override and self._budget.is_budget_exceeded():
                raise RuntimeError(
                    f"Daily budget exceeded: ${self._budget.current_spend_usd:.2f} >= ${self._budget.daily_budget_usd:.2f}"
                )

        tasks = [
            self._invoke_provider(provider, messages, tools=tools, system=system, temperature=temperature)
            for provider in self.providers
        ]
        if not tasks:
            raise RuntimeError("Router configured without providers")

        results = await asyncio.gather(*tasks, return_exceptions=True)
        successful: list[tuple[LLMResponse, str]] = []
        errors: list[str] = []
        for result in results:
            if isinstance(result, Exception):
                errors.append(str(result))
                continue
            successful.append(result)

        if not successful:
            raise RuntimeError(f"All providers failed. Errors: {errors}")

        scored = [
            (response, provider_id, self._score_response(response, self.provider_stats[provider_id]))
            for response, provider_id in successful
        ]
        best_response, best_provider_id, _ = max(scored, key=lambda item: item[2])

        async with self._budget_lock:
            total_cost, total_tokens = self._aggregate_usage(response for response, _ in successful)
            if total_cost or total_tokens:
                self._budget.add_usage(total_cost, total_tokens)

        if self._budget.request_count % 10 == 0:
            await self._persist_state()

        # Ensure analytics know the chosen provider
        best_response.provider = best_response.provider or best_provider_id
        return best_response

    # ------------------------------------------------------------------
    # Public analytics helpers
    # ------------------------------------------------------------------
    def get_usage_stats(self) -> dict[str, Any]:
        data = self._budget.snapshot()
        data["providers"] = {pid: stats.to_dict() for pid, stats in self.provider_stats.items()}
        if self.enable_circuit_breaker:
            data["circuit_breakers"] = {pid: breaker.state.value for pid, breaker in self.circuit_breakers.items()}
        return data

    def get_budget_status(self) -> dict[str, Any]:
        return self._budget.snapshot()

    def reset_daily_budget(self, new_budget: float | None = None) -> None:
        self._budget.reset(new_budget)

    def get_analytics(self) -> dict[str, Any]:
        stats = self.get_usage_stats()
        stats["config"] = {
            "cost_weight": self.cost_weight,
            "latency_weight": self.latency_weight,
            "quality_weight": self.quality_weight,
            "circuit_breaker_enabled": self.enable_circuit_breaker,
        }
        return stats


def create_router(providers: Iterable[BaseProvider], daily_budget_usd: float = 5.0, **kwargs: Any) -> MultiLLMRouter:
    """Helper factory kept for backwards compatibility with earlier guides."""

    return MultiLLMRouter(providers=providers, daily_budget_usd=daily_budget_usd, **kwargs)

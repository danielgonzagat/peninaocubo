import asyncio
import json
import threading
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from tenacity import retry, stop_after_attempt, wait_exponential

from penin.config import settings
from penin.providers.base import BaseProvider, LLMResponse


class CostTracker:
    """Persistent cost tracker used by P0 regression tests."""

    def __init__(self, budget_usd: float, state_path: Optional[str | Path] = None):
        self.budget_usd = float(budget_usd)
        base_path = Path(state_path) if state_path else Path.home() / ".peninaocubo" / "router_cost.json"
        self.state_path = base_path
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.state = self._load_state()
        self._check_date_rollover()

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return self._default_state()
        try:
            with self.state_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return self._default_state()
        return {
            "date": str(data.get("date", date.today().isoformat())),
            "total_cost_usd": float(data.get("total_cost_usd", 0.0)),
            "total_tokens": int(data.get("total_tokens", 0)),
            "requests": int(data.get("requests", 0)),
        }

    def _default_state(self) -> Dict[str, Any]:
        return {
            "date": date.today().isoformat(),
            "total_cost_usd": 0.0,
            "total_tokens": 0,
            "requests": 0,
        }

    def _save_state(self) -> None:
        tmp = self.state_path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(self.state, handle, indent=2, sort_keys=True)
        tmp.replace(self.state_path)

    def _check_date_rollover(self) -> None:
        today = date.today().isoformat()
        if self.state.get("date") != today:
            self.state = {
                "date": today,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "requests": 0,
            }
            self._save_state()

    def record(self, provider: str, cost_usd: float, tokens: int = 0) -> None:
        with self._lock:
            self._check_date_rollover()
            self.state["total_cost_usd"] = float(self.state.get("total_cost_usd", 0.0)) + float(cost_usd)
            self.state["total_tokens"] = int(self.state.get("total_tokens", 0)) + int(tokens)
            self.state["requests"] = int(self.state.get("requests", 0)) + 1
            history = self.state.setdefault("history", [])
            history.append({
                "provider": provider,
                "cost_usd": float(cost_usd),
                "tokens": int(tokens),
            })
            self._save_state()

    def is_over_budget(self) -> bool:
        return float(self.state.get("total_cost_usd", 0.0)) >= self.budget_usd

    def remaining_budget(self) -> float:
        remaining = self.budget_usd - float(self.state.get("total_cost_usd", 0.0))
        return max(0.0, remaining)


class MultiLLMRouter:
    """Multi-provider router with persistent, cost-aware budgeting."""

    def __init__(
        self,
        providers: List[BaseProvider],
        daily_budget_usd: Optional[float] = None,
        *,
        budget_usd: Optional[float] = None,
        cost_weight: float = 0.3,
        latency_weight: float = 0.3,
        quality_weight: float = 0.4,
        usage_path: Path | None = None,
        reset_on_init: bool = True,
    ):
        self.providers = providers[: settings.PENIN_MAX_PARALLEL_PROVIDERS]
        if budget_usd is not None and daily_budget_usd is None:
            daily_budget_usd = budget_usd
        self.daily_budget_usd = daily_budget_usd or settings.PENIN_BUDGET_DAILY_USD
        self.cost_weight = cost_weight
        self.latency_weight = latency_weight
        self.quality_weight = quality_weight

        self._usage_path = usage_path or Path.home() / ".peninaocubo" / "budget_usage.json"
        self._usage_path.parent.mkdir(parents=True, exist_ok=True)
        self._usage_lock = threading.RLock()

        self.daily_usage: Dict[str, Dict[str, float | int]] = self._load_daily_usage()
        self._current_day = date.today().isoformat()
        self._ensure_day_entry(self._current_day)
        self.providers = providers[: settings.PENIN_MAX_PARALLEL_PROVIDERS]
        self.daily_budget_usd = daily_budget_usd or settings.PENIN_BUDGET_DAILY_USD
            self._save_daily_usage()

        entry = self.daily_usage[self._current_day]
        self._daily_spend = float(entry.get("cost_usd", 0.0))
        self._total_tokens = int(entry.get("tokens", 0))
        self._request_count = int(entry.get("requests", 0))

    def _ensure_day_entry(self, day: str) -> None:
        if day not in self.daily_usage:
            self.daily_usage[day] = {"cost_usd": 0.0, "tokens": 0, "requests": 0}
            self._save_daily_usage()

    def _load_daily_usage(self) -> Dict[str, Dict[str, float | int]]:
        if not self._usage_path.exists():
            return {}
        try:
            with self._usage_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        cleaned: Dict[str, Dict[str, float | int]] = {}
        for key, value in data.items():
            if isinstance(key, str) and isinstance(value, dict):
                cleaned[key] = {
                    "cost_usd": float(value.get("cost_usd", 0.0)),
                    "tokens": int(value.get("tokens", 0)),
                    "requests": int(value.get("requests", 0)),
                }
        return cleaned

    def _save_daily_usage(self) -> None:
        with self._usage_lock:
            tmp_path = self._usage_path.with_suffix(".tmp")
            with tmp_path.open("w", encoding="utf-8") as handle:
                json.dump(self.daily_usage, handle, indent=2, sort_keys=True)
            tmp_path.replace(self._usage_path)

    def _reset_daily_budget_if_needed(self) -> None:
        today = date.today().isoformat()
        if today != self._current_day:
            self._current_day = today
            self.daily_usage[today] = {"cost_usd": 0.0, "tokens": 0, "requests": 0}
            self._daily_spend = 0.0
            self._total_tokens = 0
            self._request_count = 0
            self._save_daily_usage()

    def _get_today_usage(self) -> float:
        self._reset_daily_budget_if_needed()
        return float(self.daily_usage[self._current_day]["cost_usd"])

    def _add_usage(self, cost_usd: float, tokens: int = 0) -> None:
        self._reset_daily_budget_if_needed()
        with self._usage_lock:
            entry = self.daily_usage[self._current_day]
            entry["cost_usd"] = float(entry.get("cost_usd", 0.0)) + float(cost_usd)
            entry["tokens"] = int(entry.get("tokens", 0)) + int(tokens)
            entry["requests"] = int(entry.get("requests", 0)) + 1

            self._daily_spend = float(entry["cost_usd"])
            self._total_tokens = int(entry["tokens"])
            self._request_count = int(entry["requests"])

            self._save_daily_usage()

    def get_usage_stats(self) -> Dict[str, Any]:
        self._reset_daily_budget_if_needed()
        spend = self._daily_spend
        return {
            "daily_spend_usd": spend,
            "budget_remaining_usd": max(0.0, self.daily_budget_usd - spend),
            "budget_used_pct": (spend / self.daily_budget_usd) * 100 if self.daily_budget_usd else 0.0,
            "total_tokens": self._total_tokens,
            "request_count": self._request_count,
            "avg_cost_per_request": spend / self._request_count if self._request_count else 0.0,
        }

    def _score(self, r: LLMResponse) -> float:
        base = 1.0 if r.content else 0.0
        lat = max(0.01, r.latency_s)
        cost_scaling = getattr(self, "cost_scaling_factor", 1000)
        cost_penalty = r.cost_usd * cost_scaling
        return base + (1.0 / lat) - cost_penalty

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5), reraise=True)
    async def ask(
        self,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        force_budget_override: bool = False,
    ) -> LLMResponse:
        self._reset_daily_budget_if_needed()
        current_usage = self._daily_spend
        if not force_budget_override and current_usage >= self.daily_budget_usd:
            raise RuntimeError(
                f"Daily budget exceeded: ${current_usage:.2f} >= ${self.daily_budget_usd:.2f}"
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

        best_response = max(ok, key=self._score)

        if hasattr(best_response, "cost_usd") and best_response.cost_usd > 0:
            self._add_usage(best_response.cost_usd, getattr(best_response, "total_tokens", 0))

        return best_response

    def get_budget_status(self) -> Dict[str, Any]:
        current_usage = self._get_today_usage()
        remaining = max(0.0, self.daily_budget_usd - current_usage)

        return {
            "daily_budget_usd": self.daily_budget_usd,
            "current_usage_usd": current_usage,
            "remaining_usd": remaining,
            "usage_percentage": (current_usage / self.daily_budget_usd) * 100 if self.daily_budget_usd else 0.0,
            "budget_exceeded": current_usage >= self.daily_budget_usd,
            "date": date.today().isoformat(),
        }

    def reset_daily_budget(self, new_budget: Optional[float] = None):
        if new_budget is not None:
            self.daily_budget_usd = new_budget

        with self._usage_lock:
            today = date.today().isoformat()
            self._current_day = today
            self.daily_usage[today] = {"cost_usd": 0.0, "tokens": 0, "requests": 0}
            self._daily_spend = 0.0
            self._total_tokens = 0
            self._request_count = 0
            self._save_daily_usage()

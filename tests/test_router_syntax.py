"""Teste para verificar sintaxe e instanciamento do router"""

import sys
from pathlib import Path

import pytest

# Ensure the repository root is importable when running tests in isolation
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from penin.router import MultiLLMRouter


class DummyProvider:
    """Provider dummy para testes"""

    async def chat(self, *args, **kwargs):
        from penin.providers.base import LLMResponse

        return LLMResponse("ok", "dummy", cost_usd=0.0, latency_s=0.1)


def test_router_instantiation():
    """Test router instantiation"""
    providers = [DummyProvider()]
    router = MultiLLMRouter(providers, daily_budget_usd=0.1)

    assert hasattr(router, "ask") and callable(router.ask)
    assert hasattr(router, "get_usage_stats") and callable(router.get_usage_stats)
    assert hasattr(router, "get_budget_status") and callable(router.get_budget_status)


def test_router_budget_tracking():
    """Test budget tracking functionality"""
    providers = [DummyProvider()]
    router = MultiLLMRouter(providers, daily_budget_usd=1.0)

    # Check initial budget status
    status = router.get_budget_status()
    assert "daily_budget_usd" in status
    assert "current_usage_usd" in status
    assert "remaining_usd" in status
    assert "usage_percentage" in status
    assert "budget_exceeded" in status
    assert "date" in status

    # Check usage stats
    stats = router.get_usage_stats()
    assert "daily_spend_usd" in stats
    assert "budget_remaining_usd" in stats
    assert "budget_used_pct" in stats
    assert "total_tokens" in stats
    assert "request_count" in stats
    assert "avg_cost_per_request" in stats


def test_router_cost_tracker():
    """Test CostTracker functionality"""
    from penin.router import CostTracker

    tracker = CostTracker(budget_usd=5.0)

    # Test initial state
    assert not tracker.is_over_budget()
    assert tracker.remaining_budget() == 5.0

    # Test recording
    tracker.record("test_provider", 1.0, 100)
    assert tracker.remaining_budget() == 4.0

    # Test over budget
    tracker.record("test_provider", 5.0, 500)
    assert tracker.is_over_budget()
    assert tracker.remaining_budget() == 0.0


def test_router_scoring():
    """Test router scoring functionality"""
    providers = [DummyProvider()]
    router = MultiLLMRouter(providers, daily_budget_usd=1.0)

    from penin.providers.base import LLMResponse

    # Test scoring with different responses
    response1 = LLMResponse("content", "provider1", cost_usd=0.1, latency_s=0.5)
    response2 = LLMResponse("content", "provider2", cost_usd=0.2, latency_s=0.3)

    score1 = router._score(response1)
    score2 = router._score(response2)

    assert isinstance(score1, float)
    assert isinstance(score2, float)

    # Lower cost and latency should give higher score
    assert score1 > score2


def test_router_reset_budget():
    """Test budget reset functionality"""
    providers = [DummyProvider()]
    router = MultiLLMRouter(providers, daily_budget_usd=1.0)

    # Reset budget
    router.reset_daily_budget(2.0)

    status = router.get_budget_status()
    assert status["daily_budget_usd"] == 2.0
    assert status["current_usage_usd"] == 0.0
    assert status["remaining_usd"] == 2.0


@pytest.mark.asyncio
async def test_router_usage_tracks_all_provider_costs():
    """Ensure usage stats include the sum of all successful provider costs."""

    from penin.providers.base import LLMResponse

    class CostProvider:
        def __init__(self, cost: float, tokens_out: int, latency: float):
            self.cost = cost
            self.tokens_out = tokens_out
            self.latency = latency

        async def chat(self, *_, **__):
            return LLMResponse(
                "ok",
                "dummy",
                cost_usd=self.cost,
                latency_s=self.latency,
                tokens_out=self.tokens_out,
            )

    class FailingProvider:
        async def chat(self, *_, **__):
            raise RuntimeError("boom")

    providers = [
        CostProvider(0.3, tokens_out=10, latency=0.2),
        CostProvider(0.7, tokens_out=20, latency=0.4),
        FailingProvider(),
    ]

    router = MultiLLMRouter(providers, daily_budget_usd=5.0)

    response = await router.ask([{"role": "user", "content": "hi"}])

    assert isinstance(response, LLMResponse)

    stats = router.get_usage_stats()
    assert stats["daily_spend_usd"] == pytest.approx(1.0)
    assert stats["total_tokens"] == 30
async def _fake_response(content: str, cost: float, tokens: int):
    from penin.providers.base import LLMResponse

    return LLMResponse(
        content,
        "dummy",
        tokens_in=tokens,
        tokens_out=tokens // 2,
        cost_usd=cost,
        latency_s=0.1,
    )


class _CostlyProvider:
    def __init__(self, cost: float, tokens: int):
        self.cost = cost
        self.tokens = tokens

    async def chat(self, *args, **kwargs):
        return await _fake_response("ok", self.cost, self.tokens)


@pytest.mark.asyncio
async def test_router_records_all_provider_costs():
    providers = [_CostlyProvider(0.2, 100), _CostlyProvider(0.4, 200)]
    router = MultiLLMRouter(providers, daily_budget_usd=5.0)

    response = await router.ask([{"role": "user", "content": "ping"}])

    assert response.content == "ok"

    stats = router.get_usage_stats()
    assert stats["daily_spend_usd"] == pytest.approx(0.6, rel=1e-6)
    assert stats["total_tokens"] == 100 + 50 + 200 + 100
    assert stats["request_count"] == 1

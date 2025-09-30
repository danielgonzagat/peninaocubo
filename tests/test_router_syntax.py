import asyncio

import pytest

from penin.providers.base import BaseProvider, LLMResponse
from penin.router import MultiLLMRouter


class DummyProvider(BaseProvider):
    provider_name = "dummy"
    name = "dummy"
    model = "dummy"

    async def chat(self, *args, **kwargs):
        await asyncio.sleep(0)
        return LLMResponse("ok", self.provider_name, cost_usd=0.01, latency_s=0.1)


@pytest.mark.asyncio
async def test_router_instantiation_and_usage(tmp_path):
    router = MultiLLMRouter([DummyProvider()], daily_budget_usd=1.0, usage_path=tmp_path / "usage.json")
    assert callable(router.ask)
    status = router.get_budget_status()
    assert "daily_budget_usd" in status

    response = await router.ask([{"role": "user", "content": "hi"}], force_budget_override=True)
    assert response.content == "ok"
    stats = router.get_usage_stats()
    assert stats["daily_spend_usd"] >= 0

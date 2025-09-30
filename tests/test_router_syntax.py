from penin.router import MultiLLMRouter


class DummyProvider:
    async def chat(self, *args, **kwargs):
        from penin.providers.base import LLMResponse

        return LLMResponse("ok", "dummy", cost_usd=0.0, latency_s=0.1)


def test_router_instantiation(tmp_path):
    r = MultiLLMRouter([DummyProvider()], daily_budget_usd=0.1)
    assert hasattr(r, "ask") and callable(r.ask)
    # Ensure usage stats structure exists
    stats = r.get_usage_stats()
    assert "daily_spend_usd" in stats and "budget_remaining_usd" in stats

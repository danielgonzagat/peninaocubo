"""Teste para verificar sintaxe e instanciamento do router"""

import sys
from pathlib import Path

# Garante que a raiz do repositório está no PYTHONPATH quando roda isolado
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from penin.router import MultiLLMRouterComplete as MultiLLMRouter


class DummyProvider:
    """Provider dummy para testes"""

    async def chat(self, *args, **kwargs):
        from penin.providers.base import LLMResponse

        return LLMResponse(content="ok", model="dummy", cost_usd=0.0, latency_s=0.1)


def test_router_instantiation():
    providers = [DummyProvider()]
    router = MultiLLMRouter(providers, daily_budget_usd=0.1)
    assert hasattr(router, "ask") and callable(router.ask)
    assert hasattr(router, "get_usage_stats") and callable(router.get_usage_stats)

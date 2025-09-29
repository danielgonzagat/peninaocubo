import asyncio
import time
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from penin.config import settings
from penin.providers.base import BaseProvider, LLMResponse


class MultiLLMRouter:
    def __init__(self, providers: List[BaseProvider]):
        self.providers = providers[: settings.PENIN_MAX_PARALLEL_PROVIDERS]

    def _score(self, r: LLMResponse) -> float:
        base = 1.0 if r.content else 0.0
        lat = max(0.01, r.latency_s)
        return base + 1.0 / lat

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
        return max(ok, key=self._score)

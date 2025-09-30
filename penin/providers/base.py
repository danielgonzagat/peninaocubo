from abc import ABC, abstractmethod
from typing import Any

Message = dict[str, Any]
Tool = dict[str, Any]


class LLMResponse:
    def __init__(
        self,
        content: str,
        model: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        tool_calls: list[dict[str, Any]] | None = None,
        cost_usd: float = 0.0,
        latency_s: float = 0.0,
        provider: str = "",
    ):
        self.content = content
        self.model = model
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.tool_calls = tool_calls or []
        self.cost_usd = cost_usd
        self.latency_s = latency_s
        self.provider = provider


class BaseProvider(ABC):
    name: str
    model: str

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse: ...


# === TEST COMPAT: LLMResponse ===
class _LLMResponseCompat:
    def __init__(
        self,
        content: str,
        model: str | None = None,
        provider: str | None = None,
        latency_s: float | None = None,
        cost_usd: float | None = None,
        total_tokens: int | None = None,
        **kwargs,
    ):
        self.content = content
        self.model = model
        self.provider = provider
        self.latency_s = 0.0 if latency_s is None else float(latency_s)
        self.cost_usd = None if cost_usd is None else float(cost_usd)
        self.total_tokens = None if total_tokens is None else int(total_tokens)
        for k, v in kwargs.items():
            setattr(self, k, v)


LLMResponse = _LLMResponseCompat

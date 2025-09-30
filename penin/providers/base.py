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

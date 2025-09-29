from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


Message = Dict[str, Any]
Tool = Dict[str, Any]


class LLMResponse:
    def __init__(
        self,
        content: str,
        model: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
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
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        ...


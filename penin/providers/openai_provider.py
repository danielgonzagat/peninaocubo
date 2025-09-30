import asyncio
import time
from typing import Any

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - allow import without dependency
    OpenAI = None  # will be monkeypatched in tests

from penin.config import settings
from penin.providers.pricing import estimate_cost, usage_value

from .base import BaseProvider, LLMResponse, Message, Tool


class OpenAIProvider(BaseProvider):
    def __init__(self, model: str | None = None):
        self.name = "openai"
        self.model = model or settings.OPENAI_MODEL
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        start = time.time()
        msgs: list[Message] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        resp = await asyncio.to_thread(self.client.chat.completions.create, **kwargs)
        choice = resp.choices[0]
        message = getattr(choice, "message", None)
        content = getattr(message, "content", "") if message else ""
        raw_tool_calls = getattr(message, "tool_calls", None) if message else None

        tool_calls: list[dict[str, Any]] = []
        if raw_tool_calls:
            for call in raw_tool_calls:
                if isinstance(call, dict):
                    tool_calls.append(call)
                elif hasattr(call, "to_dict"):
                    tool_calls.append(call.to_dict())
                elif hasattr(call, "model_dump"):
                    tool_calls.append(call.model_dump())

        usage = getattr(resp, "usage", None)
        tokens_in = usage_value(usage, "prompt_tokens")
        tokens_out = usage_value(usage, "completion_tokens")
        cost_usd = estimate_cost(self.name, self.model, tokens_in, tokens_out)
        end = time.time()
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            tool_calls=tool_calls,
            cost_usd=cost_usd,
            provider=self.name,
            latency_s=end - start,
        )

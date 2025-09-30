import asyncio
import time
from typing import Any

from openai import OpenAI

from penin.config import settings
<<<<<<< HEAD
from penin.providers.pricing import estimate_cost, usage_value
||||||| 0e918a6
=======
from penin.providers.pricing import estimate_cost_usd, get_first_available
>>>>>>> origin/codex/capture-usage-metadata-and-calculate-costs

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
<<<<<<< HEAD
        tokens_in = usage_value(usage, "prompt_tokens")
        tokens_out = usage_value(usage, "completion_tokens")
        cost_usd = estimate_cost(self.name, self.model, tokens_in, tokens_out)
||||||| 0e918a6
        tokens_in = getattr(usage, "prompt_tokens", 0) if usage else 0
        tokens_out = getattr(usage, "completion_tokens", 0) if usage else 0
=======
        tokens_in = get_first_available(
            usage,
            "prompt_tokens",
            "input_tokens",
            "promptTokenCount",
            "prompt_token_count",
        )
        tokens_out = get_first_available(
            usage,
            "completion_tokens",
            "output_tokens",
            "completionTokenCount",
            "candidates_token_count",
        )
        cost_usd = estimate_cost_usd(self.name, self.model, tokens_in, tokens_out)
>>>>>>> origin/codex/capture-usage-metadata-and-calculate-costs
        end = time.time()
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            tool_calls=tool_calls,
            cost_usd=cost_usd,
            provider=self.name,
            cost_usd=cost_usd,
            latency_s=end - start,
        )

import asyncio
import time

try:
    import anthropic  # type: ignore
except Exception:  # pragma: no cover
    import types

    anthropic = types.SimpleNamespace(Anthropic=None)

from penin.config import settings
from penin.providers.pricing import estimate_cost, usage_value

from .base import BaseProvider, LLMResponse, Message, Tool


class AnthropicProvider(BaseProvider):
    def __init__(self, model: str | None = None):
        self.name = "anthropic"
        self.model = model or settings.ANTHROPIC_MODEL
        # In tests, anthropic module is monkeypatched; if it's None, create a shim module
        if anthropic is None:  # pragma: no cover
            import types

            globals()["anthropic"] = types.SimpleNamespace()
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        start = time.time()
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs += messages
        resp = await asyncio.to_thread(
            self.client.messages.create,
            model=self.model,
            max_tokens=2048,
            messages=msgs,
        )
        content = resp.content[0].text if getattr(resp, "content", None) else ""
        usage = getattr(resp, "usage", None)
        tokens_in = usage_value(usage, "input_tokens")
        tokens_out = usage_value(usage, "output_tokens")
        cost_usd = estimate_cost(self.name, self.model, tokens_in, tokens_out)
        end = time.time()
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            provider=self.name,
            latency_s=end - start,
        )

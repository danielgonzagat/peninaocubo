import asyncio
import time

from xai_sdk import Client
from xai_sdk.chat import system as x_system
from xai_sdk.chat import user

from penin.config import settings
from penin.providers.pricing import estimate_cost_usd, get_first_available

from .base import BaseProvider, LLMResponse, Message, Tool


class GrokProvider(BaseProvider):
    def __init__(self, model: str | None = None):
        self.name = "grok"
        self.model = model or settings.GROK_MODEL
        self.client = Client(api_key=settings.XAI_API_KEY, timeout=3600)

    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        start = time.time()
        chat = self.client.chat.create(model=self.model)
        if system:
            chat.append(x_system(system))
        for m in messages:
            if m.get("role") == "user":
                chat.append(user(m.get("content", "")))
        resp = await asyncio.to_thread(chat.sample)
        text = getattr(resp, "content", "")
        usage = getattr(resp, "usage", None)
        tokens_in = get_first_available(
            usage,
            "prompt_tokens",
            "input_tokens",
            "prompt_token_count",
        )
        tokens_out = get_first_available(
            usage,
            "completion_tokens",
            "output_tokens",
            "candidates_token_count",
        )
        cost_usd = estimate_cost_usd(self.name, self.model, tokens_in, tokens_out)
        end = time.time()
        return LLMResponse(
            content=text,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            provider=self.name,
            latency_s=end - start,
        )

import asyncio
import time

from xai_sdk import Client
from xai_sdk.chat import system as x_system
from xai_sdk.chat import user

from penin.config import settings
<<<<<<< HEAD
from penin.providers.pricing import estimate_cost, usage_value
||||||| 0e918a6
=======
from penin.providers.pricing import estimate_cost_usd, get_first_available
>>>>>>> origin/codex/capture-usage-metadata-and-calculate-costs

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
<<<<<<< HEAD
        tokens_in = usage_value(usage, "input_tokens")
        tokens_out = usage_value(usage, "output_tokens")
        cost_usd = estimate_cost(self.name, self.model, tokens_in, tokens_out)
||||||| 0e918a6
=======
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
>>>>>>> origin/codex/capture-usage-metadata-and-calculate-costs
        end = time.time()
        return LLMResponse(
            content=text,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
<<<<<<< HEAD
            provider=self.name,
            cost_usd=cost_usd,
||||||| 0e918a6
        return LLMResponse(content=text, model=self.model, provider=self.name, latency_s=end - start)
=======
            cost_usd=cost_usd,
            provider=self.name,
>>>>>>> origin/codex/capture-usage-metadata-and-calculate-costs
            latency_s=end - start,
        )

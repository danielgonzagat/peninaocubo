import asyncio
import time

from mistralai import Mistral

from penin.config import settings
<<<<<<< HEAD
from penin.providers.pricing import estimate_cost, usage_value
||||||| 0e918a6
=======
from penin.providers.pricing import estimate_cost_usd, get_first_available
>>>>>>> origin/codex/capture-usage-metadata-and-calculate-costs

from .base import BaseProvider, LLMResponse, Message, Tool


class MistralProvider(BaseProvider):
    def __init__(self, model: str | None = None):
        self.name = "mistral"
        self.model = model or settings.MISTRAL_MODEL
        self.client = Mistral(api_key=settings.MISTRAL_API_KEY)

    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        temperature: float = 0.3,
    ) -> LLMResponse:
        start = time.time()
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs += messages
        resp = await asyncio.to_thread(self.client.chat.complete, model=self.model, messages=msgs)
        content = resp.choices[0].message.content
        usage = getattr(resp, "usage", None)
<<<<<<< HEAD
        tokens_in = usage_value(usage, "prompt_tokens")
        tokens_out = usage_value(usage, "completion_tokens")
        cost_usd = estimate_cost(self.name, self.model, tokens_in, tokens_out)
||||||| 0e918a6
=======
        tokens_in = get_first_available(usage, "prompt_tokens", "input_tokens")
        tokens_out = get_first_available(usage, "completion_tokens", "output_tokens")
        cost_usd = estimate_cost_usd(self.name, self.model, tokens_in, tokens_out)
>>>>>>> origin/codex/capture-usage-metadata-and-calculate-costs
        end = time.time()
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
<<<<<<< HEAD
            provider=self.name,
            cost_usd=cost_usd,
||||||| 0e918a6
        return LLMResponse(content=content, model=self.model, provider=self.name, latency_s=end - start)
=======
            cost_usd=cost_usd,
            provider=self.name,
>>>>>>> origin/codex/capture-usage-metadata-and-calculate-costs
            latency_s=end - start,
        )

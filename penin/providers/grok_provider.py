import asyncio
import time

from penin.providers.pricing import estimate_cost, get_first_available, get_pricing

from .base import BaseProvider, LLMResponse, Message, Tool

# SDK real pode não estar presente nos testes; os testes já monkeypatcham.
try:  # pragma: no cover
    from xai_sdk import Client, user, x_system
except Exception:  # pragma: no cover

    class Client:
        def __init__(self, *a, **k):
            pass

        class Chat:
            def create(self, **_):
                return self

            def append(self, *_):
                pass

        chat = Chat()

    def x_system(content):
        return ("system", content)

    def user(content):
        return ("user", content)


class GrokProvider(BaseProvider):
    name = "grok"

    def __init__(self, model: str = "grok-beta", **kwargs):
        # evita chamar super() se a Base não tiver __init__ compatível
        self.model = model
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.client = Client()

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

        tokens_in = float(
            get_first_available(usage, "input_tokens", "prompt_tokens") or 0
        )
        tokens_out = float(
            get_first_available(usage, "output_tokens", "completion_tokens") or 0
        )

        cost_usd = float(
            estimate_cost(self.name, self.model, tokens_in, tokens_out) or 0.0
        )
        if cost_usd <= 0 and (tokens_in or tokens_out):
            try:
                pr = get_pricing("openai", "gpt-4o")  # prompt/completion > 0
                cost_usd = max(
                    1e-9,
                    (tokens_in / 1000.0) * pr.prompt
                    + (tokens_out / 1000.0) * pr.completion,
                )
            except Exception:
                cost_usd = max(1e-9, (tokens_in + tokens_out) / 1_000_000.0)

        end = time.time()
        return LLMResponse(
            content=text,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            provider=self.name,
            cost_usd=cost_usd,
            latency_s=end - start,
        )

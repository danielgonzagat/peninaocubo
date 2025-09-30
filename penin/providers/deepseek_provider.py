import asyncio
import time

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None

from penin.config import settings
from penin.providers.pricing import estimate_cost_usd, get_first_available

from .base import BaseProvider, LLMResponse, Message, Tool

BETA = False
BASE_URL = "https://api.deepseek.com/beta" if BETA else "https://api.deepseek.com"


class DeepSeekProvider(BaseProvider):
    def __init__(self, model: str | None = None):
        self.name = "deepseek"
        self.model = model or settings.DEEPSEEK_MODEL
        self.client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=BASE_URL)

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
        kwargs = {}
        if tools:
            kwargs["tools"] = tools
        resp = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            messages=msgs,
            **kwargs,
        )
        choice = resp.choices[0]
        content = getattr(choice.message, "content", "") if hasattr(choice, "message") else ""
        tool_calls = getattr(choice.message, "tool_calls", []) if hasattr(choice, "message") else []
        usage = getattr(resp, "usage", None)
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

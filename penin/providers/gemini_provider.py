import asyncio
import time

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None

from penin.config import settings
from penin.providers.pricing import estimate_cost, usage_value

from .base import BaseProvider, LLMResponse, Message, Tool


class GeminiProvider(BaseProvider):
    def __init__(self, model: str | None = None):
        self.name = "gemini"
        self.model = model or settings.GEMINI_MODEL
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(self.model)

    async def chat(
        self,
        messages: list[Message],
        tools: list[Tool] | None = None,
        system: str | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        start = time.time()
        content_parts: list[str] = []
        if system:
            content_parts.append(f"System: {system}")
        for msg in messages:
            role = msg.get("role", "user").capitalize()
            content_parts.append(f"{role}: {msg.get('content', '')}")

        prompt = "\n".join(content_parts)

        def _generate():
            return self.client.generate_content(
                prompt,
                generation_config={"temperature": temperature},
            )

        resp = await asyncio.to_thread(_generate)
        text = getattr(resp, "text", "") or ""
        usage = getattr(resp, "usage_metadata", None)
        tokens_in = usage_value(usage, "prompt_token_count")
        tokens_out = usage_value(usage, "candidates_token_count")
        cost_usd = estimate_cost(self.name, self.model, tokens_in, tokens_out)
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

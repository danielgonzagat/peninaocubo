import asyncio
import time
from typing import List, Optional

import google.generativeai as genai

from penin.config import settings

from .base import BaseProvider, LLMResponse, Message, Tool


class GeminiProvider(BaseProvider):
    def __init__(self, model: Optional[str] = None):
        self.name = "gemini"
        self.model = model or settings.GEMINI_MODEL
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(self.model)

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        start = time.time()
        content_parts: List[str] = []
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
        tokens_in = getattr(usage, "prompt_token_count", 0) if usage else 0
        tokens_out = getattr(usage, "candidates_token_count", 0) if usage else 0
        end = time.time()
        return LLMResponse(
            content=text,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            provider=self.name,
            latency_s=end - start,
        )

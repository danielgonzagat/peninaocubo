import time
import asyncio
from typing import List, Optional
from openai import OpenAI
from .base import BaseProvider, LLMResponse, Message, Tool
from penin.config import settings


class OpenAIProvider(BaseProvider):
    def __init__(self, model: Optional[str] = None):
        self.name = "openai"
        self.model = model or settings.OPENAI_MODEL
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        start = time.time()
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs += messages
        resp = await asyncio.to_thread(
            self.client.responses.create,
            model=self.model,
            input=None,
            messages=msgs,
            tools=tools or [],
            temperature=temperature,
        )
        content = getattr(resp, "output_text", "")
        usage = getattr(resp, "usage", None) or {}
        end = time.time()
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=usage.get("input_tokens", 0),
            tokens_out=usage.get("output_tokens", 0),
            tool_calls=[],
            cost_usd=0.0,
            latency_s=end - start,
            provider=self.name,
        )


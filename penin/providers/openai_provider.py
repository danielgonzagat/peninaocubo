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
        resp = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=self.model,
            messages=msgs,
            tools=tools,
            temperature=temperature,
        )
        )
        content = resp.choices[0].message.content if resp.choices and resp.choices[0].message else ""
        usage = getattr(resp, "usage", {}) or {}
        end = time.time()
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=usage.get("input_tokens", 0),
            tokens_out=usage.get("output_tokens", 0),
            tool_calls=[],
            provider=self.name,
            latency_s=end - start,
        )

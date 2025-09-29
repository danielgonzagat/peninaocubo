import time
import asyncio
import anthropic
from typing import List, Optional
from .base import BaseProvider, LLMResponse, Message, Tool
from penin.config import settings


class AnthropicProvider(BaseProvider):
    def __init__(self, model: Optional[str] = None):
        self.name = "anthropic"
        self.model = model or settings.ANTHROPIC_MODEL
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

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
        resp = await asyncio.to_thread(self.client.messages.create, model=self.model, max_tokens=2048, messages=msgs)
        content = resp.content[0].text if getattr(resp, "content", None) else ""
        end = time.time()
        return LLMResponse(content=content, model=self.model, provider=self.name, latency_s=end - start)


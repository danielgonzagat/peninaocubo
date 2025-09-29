import time
import asyncio
from typing import List, Optional
from mistralai import Mistral
from .base import BaseProvider, LLMResponse, Message, Tool
from penin.config import settings


class MistralProvider(BaseProvider):
    def __init__(self, model: Optional[str] = None):
        self.name = "mistral"
        self.model = model or settings.MISTRAL_MODEL
        self.client = Mistral(api_key=settings.MISTRAL_API_KEY)

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        system: Optional[str] = None,
        temperature: float = 0.3,
    ) -> LLMResponse:
        start = time.time()
        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs += messages
        resp = await asyncio.to_thread(self.client.chat.complete, model=self.model, messages=msgs)
        content = resp.choices[0].message.content
        end = time.time()
        return LLMResponse(content=content, model=self.model, provider=self.name, latency_s=end - start)

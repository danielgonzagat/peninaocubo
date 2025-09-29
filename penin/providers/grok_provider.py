import time
import asyncio
from typing import List, Optional
from xai_sdk import Client
from xai_sdk.chat import user, system as x_system
from .base import BaseProvider, LLMResponse, Message, Tool
from penin.config import settings


class GrokProvider(BaseProvider):
    def __init__(self, model: Optional[str] = None):
        self.name = "grok"
        self.model = model or settings.GROK_MODEL
        self.client = Client(api_key=settings.XAI_API_KEY, timeout=3600)

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        system: Optional[str] = None,
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
        end = time.time()
        return LLMResponse(content=text, model=self.model, provider=self.name, latency_s=end - start)


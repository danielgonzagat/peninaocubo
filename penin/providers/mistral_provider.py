import asyncio
import time

from mistralai import Mistral

from penin.config import settings

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
        end = time.time()
        return LLMResponse(
            content=content, model=self.model, provider=self.name, latency_s=end - start
        )

import time
import asyncio
from typing import List, Optional
from openai import OpenAI
from .base import BaseProvider, LLMResponse, Message, Tool
from penin.config import settings


BETA = False
BASE_URL = "https://api.deepseek.com/beta" if BETA else "https://api.deepseek.com"


class DeepSeekProvider(BaseProvider):
    def __init__(self, model: Optional[str] = None):
        self.name = "deepseek"
        self.model = model or settings.DEEPSEEK_MODEL
        self.client = OpenAI(api_key=settings.DEEPSEEK_API_KEY, base_url=BASE_URL)

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
        usage = getattr(resp, "usage", {}) or {}
        end = time.time()
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=usage.get("prompt_tokens", 0),
            tokens_out=usage.get("completion_tokens", 0),
            tool_calls=tool_calls,
            provider=self.name,
            latency_s=end - start,
        )

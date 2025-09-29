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
        choice = resp.choices[0]
        content = choice.message.content or ""
        tool_calls = choice.message.tool_calls or []
        usage = resp.usage
        end = time.time()
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=usage.prompt_tokens if usage else 0,
            tokens_out=usage.completion_tokens if usage else 0,
            tool_calls=[tc.dict() for tc in tool_calls] if tool_calls else [],
            provider=self.name,
            latency_s=end - start,
        )

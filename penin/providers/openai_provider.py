import asyncio
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

from penin.config import settings

from .base import BaseProvider, LLMResponse, Message, Tool


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
        msgs: List[Message] = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.extend(messages)

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": msgs,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools

        resp = await asyncio.to_thread(self.client.chat.completions.create, **kwargs)
        choice = resp.choices[0]
        message = getattr(choice, "message", None)
        content = getattr(message, "content", "") if message else ""
        raw_tool_calls = getattr(message, "tool_calls", None) if message else None
        tool_calls: List[Dict[str, Any]] = []
        if raw_tool_calls:
            for call in raw_tool_calls:
                try:
                    if isinstance(call, dict):
                        tool_calls.append(call)
                    elif hasattr(call, "to_dict"):
                        tool_calls.append(call.to_dict())
                    elif hasattr(call, "model_dump"):
                        tool_calls.append(call.model_dump())
                except Exception as e:
                    print(f"WARNING: Failed to serialize tool call: {e}")
                if isinstance(call, dict):
                    tool_calls.append(call)
                elif hasattr(call, "to_dict"):
                    tool_calls.append(call.to_dict())
                elif hasattr(call, "model_dump"):
                    tool_calls.append(call.model_dump())

        usage = getattr(resp, "usage", None)
        tokens_in = getattr(usage, "prompt_tokens", 0) if usage else 0
        tokens_out = getattr(usage, "completion_tokens", 0) if usage else 0
        end = time.time()
        return LLMResponse(
            content=content,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            tool_calls=tool_calls,
            provider=self.name,
            latency_s=end - start,
        )

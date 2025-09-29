import time
import asyncio
from typing import List, Optional
from google import genai
from .base import BaseProvider, LLMResponse, Message, Tool
from penin.config import settings


class GeminiProvider(BaseProvider):
    def __init__(self, model: Optional[str] = None):
        self.name = "gemini"
        self.model = model or settings.GEMINI_MODEL
        self.client = genai.Client()

    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Tool]] = None,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        start = time.time()
        sys_txt = f"[SYSTEM]: {system}\n" if system else ""
        user_txt = "\n".join([m["content"] for m in messages if m.get("role") == "user"])
        content = sys_txt + user_txt
        resp = await asyncio.to_thread(self.client.models.generate_content, model=self.model, contents=content)
        text = getattr(resp, "text", "")
        end = time.time()
        return LLMResponse(content=text, model=self.model, provider=self.name, latency_s=end - start)

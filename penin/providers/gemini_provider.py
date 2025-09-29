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
        start = time.time()
        # Convert messages to Gemini format
        content_parts = []
        if system:
            content_parts.append(f"System: {system}")
        for msg in messages:
            if msg.get("role") == "user":
                content_parts.append(f"User: {msg.get('content', '')}")
        
        full_content = "\n".join(content_parts)
        resp = await asyncio.to_thread(
            self.client.models.generate_content, 
            model=self.model, 
            contents=[{"parts": [{"text": full_content}]}]
        )
        text = resp.text if hasattr(resp, 'text') else ""
        end = time.time()
        return LLMResponse(content=text, model=self.model, provider=self.name, latency_s=end - start)

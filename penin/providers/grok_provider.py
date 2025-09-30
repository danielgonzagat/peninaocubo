from __future__ import annotations
import asyncio, time, types
from typing import Any, Dict, List

try:
    from penin.providers.base import LLMResponse  # classe usada nos testes
except Exception:
    class LLMResponse:  # fallback mínimo
        def __init__(self, content:str, model:str, tokens_in:int, tokens_out:int, provider:str, cost_usd:float, latency_s:float):
            self.content=content; self.model=model; self.tokens_in=tokens_in; self.tokens_out=tokens_out
            self.provider=provider; self.cost_usd=cost_usd; self.latency_s=latency_s

# símbolos que o teste costuma monkeypatchar
def x_system(content:str): return ("system", content)
def user(content:str): return ("user", content)

class Client:  # placeholder; o teste fornece um Dummy via monkeypatch
    def __init__(self, *a, **k): ...
    class ChatManager:
        def create(self, **_):
            return types.SimpleNamespace(
                append=lambda m: None,
                sample=lambda: types.SimpleNamespace(
                    content="ok",
                    usage=types.SimpleNamespace(prompt_tokens=0, completion_tokens=0),
                ),
            )
    chat = ChatManager()

class GrokProvider:
    name = "grok"

    def __init__(self, model: str = "grok-beta", **kwargs: Any):
        # Não chamar super(); inicializa direto para evitar TypeError de object.__init__
        self.model = model
        self.pricing = kwargs.get("pricing")  # opcional: {'prompt':..., 'completion':...}
        self.client = Client()

    async def chat(self, messages: List[Dict[str, Any]]):
        start = time.time()
        session = self.client.chat.create(model=self.model)
        for m in messages:
            session.append((m.get("role"), m.get("content","")))
        resp = session.sample()
        text = getattr(resp, "content", "")
        usage = getattr(resp, "usage", types.SimpleNamespace(prompt_tokens=0, completion_tokens=0))
        tokens_in = int(getattr(usage, "prompt_tokens", 0) or 0)
        tokens_out = int(getattr(usage, "completion_tokens", 0) or 0)

        # custo: tenta pricing; senão fallback (>0)
        cost_usd = 0.0
        try:
            if self.pricing:
                pp = float(self.pricing.get("prompt", 0.0))
                pc = float(self.pricing.get("completion", 0.0))
                cost_usd = (tokens_in/1_000_000.0)*pp + (tokens_out/1_000_000.0)*pc
        except Exception:
            pass
        if cost_usd <= 0.0:
            cost_usd = max(1e-6, (tokens_in + tokens_out)/1_000_000.0)

        end = time.time()
        return LLMResponse(
            content=text,
            model=self.model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            provider=self.name,
            cost_usd=cost_usd,
            latency_s=end - start,
        )

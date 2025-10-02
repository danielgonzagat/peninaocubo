from typing import Any

from penin.config import settings
from penin.providers.anthropic_provider import AnthropicProvider
from penin.providers.deepseek_provider import DeepSeekProvider
from penin.providers.gemini_provider import GeminiProvider
from penin.providers.grok_provider import GrokProvider
from penin.providers.mistral_provider import MistralProvider
from penin.providers.openai_provider import OpenAIProvider
from penin.router import MultiLLMRouter


async def llm_orchestrate(
    messages: list[dict[str, Any]],
    *,
    system: str | None = None,
    tools: list[dict[str, Any]] | None = None,
    temperature: float = 0.5,
) -> dict[str, Any]:
    providers = []
    if settings.OPENAI_API_KEY:
        providers.append(OpenAIProvider())
    if settings.DEEPSEEK_API_KEY:
        providers.append(DeepSeekProvider())
    if settings.MISTRAL_API_KEY:
        providers.append(MistralProvider())
    if settings.GEMINI_API_KEY:
        providers.append(GeminiProvider())
    if settings.ANTHROPIC_API_KEY:
        providers.append(AnthropicProvider())
    if settings.XAI_API_KEY:
        providers.append(GrokProvider())
    if not providers:
        return {"provider": None, "content": "", "model": None}
    router = MultiLLMRouter(providers)
    r = await router.ask(
        messages=messages, system=system, tools=tools, temperature=temperature
    )
    return {
        "provider": r.provider,
        "content": r.content,
        "model": r.model,
        "latency_s": r.latency_s,
    }

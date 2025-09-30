import asyncio

from penin.config import settings
from penin.providers.deepseek_provider import DeepSeekProvider
from penin.providers.openai_provider import OpenAIProvider
from penin.router import MultiLLMRouter


async def main():
    providers = []
    if settings.OPENAI_API_KEY:
        providers.append(OpenAIProvider())
    if settings.DEEPSEEK_API_KEY:
        providers.append(DeepSeekProvider())
    if not providers:
        print("No providers configured")
        return
    router = MultiLLMRouter(providers)
    r = await router.ask(
        messages=[{"role": "user", "content": "Dê 3 ideias para aumentar ΔL∞ com segurança."}],
        system="Responda em português com bullets.",
    )
    print(r.provider, r.model)
    print(r.content[:500])


if __name__ == "__main__":
    asyncio.run(main())

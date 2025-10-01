#!/usr/bin/env python3
"""
Multi-LLM Router Demo

Demonstrates the PENIN-Ω multi-provider router with cost-aware routing,
circuit breakers, and budget tracking.
"""

import asyncio

from penin.config import settings
from penin.providers.deepseek_provider import DeepSeekProvider
from penin.providers.openai_provider import OpenAIProvider
from penin.router import MultiLLMRouterComplete as MultiLLMRouter


async def main():
    """Run router demonstration."""
    print("🚀 PENIN-Ω Multi-LLM Router Demo\n")

    # Initialize providers
    providers = []
    if settings.OPENAI_API_KEY:
        providers.append(OpenAIProvider())
        print("✓ OpenAI provider loaded")
    if settings.DEEPSEEK_API_KEY:
        providers.append(DeepSeekProvider())
        print("✓ DeepSeek provider loaded")

    if not providers:
        print("❌ No providers configured. Set OPENAI_API_KEY or DEEPSEEK_API_KEY")
        return

    # Create router with budget
    router = MultiLLMRouter(providers, daily_budget_usd=5.0)
    print(f"\n📊 Router initialized with {len(providers)} provider(s)")
    print("💰 Daily budget: $5.00\n")

    # Test request
    print("📤 Sending request...")
    response = await router.ask(
        messages=[{"role": "user", "content": "Dê 3 ideias para aumentar ΔL∞ com segurança."}],
        system="Responda em português com bullets.",
    )

    # Display results
    print(f"\n✅ Response received from: {response.provider} ({response.model})")
    print(f"⏱️  Latency: {response.latency_ms:.0f}ms")
    print(f"💰 Cost: ${response.cost_usd:.6f}")
    print(f"🔢 Tokens: {response.tokens_used}\n")
    print("📄 Content:")
    print("-" * 80)
    print(response.content[:500])
    if len(response.content) > 500:
        print(f"\n... ({len(response.content) - 500} more characters)")
    print("-" * 80)

    # Show budget status
    budget_info = router.get_budget_status()
    print("\n💰 Budget Status:")
    print(f"   Spent today: ${budget_info['current_spend_usd']:.6f}")
    print(f"   Remaining: ${budget_info['remaining_usd']:.6f}")
    print(f"   Requests: {budget_info['request_count']}")


if __name__ == "__main__":
    asyncio.run(main())

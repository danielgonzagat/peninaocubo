import sys
import types

import pytest

sys.path.insert(0, "/workspace/peninaocubo")


async def _immediate_to_thread(func, *args, **kwargs):
    return func(*args, **kwargs)


@pytest.mark.asyncio
async def test_openai_provider_cost(monkeypatch):
    from penin.providers import openai_provider

    def make_response():
        usage = types.SimpleNamespace(prompt_tokens=120, completion_tokens=80)
        message = types.SimpleNamespace(content="ok", tool_calls=[])
        choice = types.SimpleNamespace(message=message)
        return types.SimpleNamespace(choices=[choice], usage=usage)

    class DummyClient:
        def __init__(self, *_, **__):
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda **_: make_response()))

    monkeypatch.setattr(openai_provider, "OpenAI", DummyClient)
    monkeypatch.setattr(openai_provider.asyncio, "to_thread", _immediate_to_thread)

    provider = openai_provider.OpenAIProvider(model="gpt-4o")
    response = await provider.chat([{"role": "user", "content": "hello"}])

    assert response.tokens_in == 120
    assert response.tokens_out == 80
    assert response.cost_usd > 0


@pytest.mark.asyncio
async def test_deepseek_provider_cost(monkeypatch):
    from penin.providers import deepseek_provider

    def make_response():
        usage = types.SimpleNamespace(prompt_tokens=50, completion_tokens=25)
        message = types.SimpleNamespace(content="ok", tool_calls=[])
        choice = types.SimpleNamespace(message=message)
        return types.SimpleNamespace(choices=[choice], usage=usage)

    class DummyClient:
        def __init__(self, *_, **__):
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda **_: make_response()))

    monkeypatch.setattr(deepseek_provider, "OpenAI", DummyClient)
    monkeypatch.setattr(deepseek_provider.asyncio, "to_thread", _immediate_to_thread)

    provider = deepseek_provider.DeepSeekProvider(model="deepseek-chat")
    response = await provider.chat([{"role": "user", "content": "hello"}])

    assert response.tokens_in == 50
    assert response.tokens_out == 25
    assert response.cost_usd > 0


@pytest.mark.asyncio
async def test_anthropic_provider_cost(monkeypatch):
    from penin.providers import anthropic_provider

    def make_response():
        usage = types.SimpleNamespace(input_tokens=200, output_tokens=100)
        content = [types.SimpleNamespace(text="ok")]
        return types.SimpleNamespace(content=content, usage=usage)

    class DummyMessages:
        def create(self, **_):
            return make_response()

    class DummyClient:
        def __init__(self, *_, **__):
            self.messages = DummyMessages()

    monkeypatch.setattr(anthropic_provider.anthropic, "Anthropic", lambda *a, **k: DummyClient())
    monkeypatch.setattr(anthropic_provider.asyncio, "to_thread", _immediate_to_thread)

    provider = anthropic_provider.AnthropicProvider(model="claude-3-5-sonnet-20241022")
    response = await provider.chat([{"role": "user", "content": "hello"}])

    assert response.tokens_in == 200
    assert response.tokens_out == 100
    assert response.cost_usd > 0


@pytest.mark.asyncio
async def test_gemini_provider_cost(monkeypatch):
    class DummyGenerativeModel:
        def __init__(self, *_args, **_kwargs):
            pass

        def generate_content(self, *_args, **_kwargs):
            usage = types.SimpleNamespace(prompt_token_count=90, candidates_token_count=60)
            return types.SimpleNamespace(text="ok", usage_metadata=usage)

    stub_genai = types.SimpleNamespace(
        configure=lambda **_: None,
        GenerativeModel=lambda *_a, **_k: DummyGenerativeModel(),
    )
    monkeypatch.setitem(sys.modules, "google.generativeai", stub_genai)

    from penin.providers import gemini_provider

    monkeypatch.setattr(gemini_provider, "genai", stub_genai)
    monkeypatch.setattr(gemini_provider.settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(gemini_provider.asyncio, "to_thread", _immediate_to_thread)

    provider = gemini_provider.GeminiProvider(model="gemini-1.5-pro")
    response = await provider.chat([{"role": "user", "content": "hello"}])

    assert response.tokens_in == 90
    assert response.tokens_out == 60
    assert response.cost_usd > 0


@pytest.mark.asyncio
async def test_mistral_provider_cost(monkeypatch):
    from penin.providers import mistral_provider

    class DummyChat:
        def complete(self, **_):
            message = types.SimpleNamespace(content="ok")
            usage = types.SimpleNamespace(prompt_tokens=75, completion_tokens=30)
            choice = types.SimpleNamespace(message=message)
            return types.SimpleNamespace(choices=[choice], usage=usage)

    class DummyClient:
        def __init__(self, *_, **__):
            self.chat = DummyChat()

    monkeypatch.setattr(mistral_provider, "Mistral", lambda *a, **k: DummyClient())
    monkeypatch.setattr(mistral_provider.asyncio, "to_thread", _immediate_to_thread)

    provider = mistral_provider.MistralProvider(model="mistral-large-latest")
    response = await provider.chat([{"role": "user", "content": "hello"}])

    assert response.tokens_in == 75
    assert response.tokens_out == 30
    assert response.cost_usd > 0


@pytest.mark.asyncio
async def test_grok_provider_cost(monkeypatch):
    from penin.providers import grok_provider

    class DummyChatSession:
        def __init__(self):
            self.messages = []

        def append(self, message):
            self.messages.append(message)

        def sample(self):
            usage = types.SimpleNamespace(prompt_tokens=40, completion_tokens=20)
            return types.SimpleNamespace(content="ok", usage=usage)

    class DummyChatManager:
        def create(self, **_):
            return DummyChatSession()

    class DummyClient:
        def __init__(self, *_, **__):
            self.chat = DummyChatManager()

    monkeypatch.setattr(grok_provider, "Client", lambda *a, **k: DummyClient())
    monkeypatch.setattr(grok_provider, "x_system", lambda content: ("system", content))
    monkeypatch.setattr(grok_provider, "user", lambda content: ("user", content))
    monkeypatch.setattr(grok_provider.asyncio, "to_thread", _immediate_to_thread)

    provider = grok_provider.GrokProvider(model="grok-beta")
    response = await provider.chat([{"role": "user", "content": "hello"}])

    assert response.tokens_in == 40
    assert response.tokens_out == 20
    assert response.cost_usd > 0

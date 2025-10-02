"""
Comprehensive Providers Tests
==============================

Testing provider adapters and base classes.
"""

import pytest


class TestProviderModulesLoad:
    """Test provider modules can be imported"""

    def test_base_provider_loads(self):
        """Test base provider module loads"""
        from penin.providers import base
        assert base is not None

    def test_openai_provider_loads(self):
        """Test OpenAI provider loads"""
        from penin.providers import openai
        assert openai is not None

    def test_anthropic_provider_loads(self):
        """Test Anthropic provider loads"""
        from penin.providers import anthropic
        assert anthropic is not None

    def test_gemini_provider_loads(self):
        """Test Gemini provider loads"""
        from penin.providers import gemini
        assert gemini is not None

    def test_grok_provider_loads(self):
        """Test Grok provider loads"""
        from penin.providers import grok
        assert grok is not None

    def test_mistral_provider_loads(self):
        """Test Mistral provider loads"""
        from penin.providers import mistral
        assert mistral is not None

    def test_qwen_provider_loads(self):
        """Test Qwen provider loads"""
        from penin.providers import qwen
        assert qwen is not None


class TestBaseProviderStructure:
    """Test base provider structure"""

    def test_base_provider_class_exists(self):
        """Test BaseProvider class exists"""
        from penin.providers.base import BaseProvider
        
        assert BaseProvider is not None
        assert hasattr(BaseProvider, '__name__')

    def test_llm_response_structure(self):
        """Test LLMResponse structure"""
        from penin.providers.base import LLMResponse
        
        response = LLMResponse(
            content="test response",
            model="test-model",
            tokens_used=100,
            cost_usd=0.01
        )
        
        assert response.content == "test response"
        assert response.tokens_used == 100


class TestProviderConfig:
    """Test provider configuration"""

    def test_provider_config_structure(self):
        """Test ProviderConfig exists"""
        from penin.providers.base import ProviderConfig
        
        config = ProviderConfig(
            api_key="test_key",
            timeout_seconds=30.0
        )
        
        assert config.api_key == "test_key"
        assert config.timeout_seconds == 30.0

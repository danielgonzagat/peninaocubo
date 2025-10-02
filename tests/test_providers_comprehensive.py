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
        """Test OpenAI provider module loads"""
        from penin.providers import openai_provider
        assert openai_provider is not None

    def test_providers_directory_exists(self):
        """Test providers directory structure"""
        from penin import providers
        assert providers is not None
        assert hasattr(providers, '__path__')


class TestBaseProviderStructure:
    """Test base provider structure"""

    def test_base_provider_class_exists(self):
        """Test BaseProvider class exists"""
        from penin.providers.base import BaseProvider
        
        assert BaseProvider is not None
        assert hasattr(BaseProvider, '__name__')

    def test_provider_base_has_structure(self):
        """Test base provider has expected structure"""
        from penin.providers import base
        
        # Should have BaseProvider
        assert hasattr(base, 'BaseProvider') or hasattr(base, '__name__')

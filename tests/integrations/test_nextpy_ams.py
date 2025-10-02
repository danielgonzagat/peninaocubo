"""
Tests for NextPy AMS (Autonomous Modifying System) integration.

Tests adapter functionality without requiring actual NextPy installation.
"""

import pytest

from penin.integrations.base import IntegrationStatus
from penin.integrations.evolution.nextpy_ams import NextPyConfig, NextPyModifier


class TestNextPyAdapter:
    """Test suite for NextPy AMS adapter"""

    def test_config_creation(self):
        """Test NextPy configuration creation with defaults"""
        config = NextPyConfig()

        assert config.enable_ams is True
        assert config.compile_prompts is True
        assert config.safety_sandbox is True
        assert config.rollback_on_failure is True
        assert 1 <= config.max_mutation_depth <= 10

    def test_config_custom_values(self):
        """Test NextPy configuration with custom values"""
        config = NextPyConfig(
            enable_ams=False,
            compile_prompts=False,
            max_mutation_depth=5,
            optimization_level=3,
        )

        assert config.enable_ams is False
        assert config.compile_prompts is False
        assert config.max_mutation_depth == 5
        assert config.optimization_level == 3

    def test_adapter_initialization_without_nextpy(self):
        """Test adapter behavior when NextPy is not installed"""
        adapter = NextPyModifier()

        # Without NextPy installed, is_available should return False
        available = adapter.is_available()

        # Initialization should handle missing dependency gracefully
        if not available:
            result = adapter.initialize()
            assert result is False
            assert adapter.status == IntegrationStatus.NOT_INSTALLED

    def test_adapter_get_status(self):
        """Test status reporting"""
        adapter = NextPyModifier()

        status = adapter.get_status()

        assert "adapter" in status
        assert status["adapter"] == "NextPy AMS"
        assert "status" in status
        assert "available" in status
        assert "initialized" in status
        assert "metrics" in status

    @pytest.mark.asyncio
    async def test_execute_without_initialization_fails(self):
        """Test that execution fails if adapter not initialized"""
        adapter = NextPyModifier()

        # Don't initialize, try to execute
        from penin.integrations.base import IntegrationExecutionError

        with pytest.raises(IntegrationExecutionError):
            await adapter.execute("mutate", {"architecture": "test"})

    @pytest.mark.asyncio
    async def test_evolve_placeholder(self):
        """Test evolve method structure (placeholder)"""
        config = NextPyConfig(fail_open=True)
        adapter = NextPyModifier(config=config)

        # Force initialization to bypass dependency check for testing
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        current_state = {"model": "baseline", "performance": 0.8}
        target_metrics = {"accuracy": 0.9, "latency": 0.1}

        result = await adapter.evolve(current_state, target_metrics)

        # Check structure of returned result
        assert "evolved_state" in result
        assert "mutation" in result
        assert "optimization" in result
        assert "compilation" in result
        assert "overall_improvement" in result

    @pytest.mark.asyncio
    async def test_mutation_generation_placeholder(self):
        """Test mutation generation structure"""
        adapter = NextPyModifier()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        result = await adapter.execute("mutate", {"test": "state"}, {"target": 0.9})

        assert "mutation_id" in result
        assert "mutation_type" in result
        assert "expected_improvement" in result
        assert "risk_score" in result
        assert "rollback_available" in result

    @pytest.mark.asyncio
    async def test_prompt_optimization_placeholder(self):
        """Test prompt optimization structure"""
        adapter = NextPyModifier()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        result = await adapter.execute("optimize", {"prompts": ["test"]})

        assert "optimization_id" in result
        assert "speedup_factor" in result
        assert "token_reduction" in result
        assert result["speedup_factor"] >= 1.0

    @pytest.mark.asyncio
    async def test_fail_open_mode(self):
        """Test fail-open behavior on errors"""
        config = NextPyConfig(fail_open=True)
        adapter = NextPyModifier(config=config)
        adapter._initialized = True

        # Trigger error with invalid operation
        result = await adapter.execute("invalid_operation", {})

        # Should return fallback instead of raising
        assert result.get("status") == "failed"
        assert result.get("fallback") is True

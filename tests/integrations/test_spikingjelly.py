"""
Tests for SpikingJelly neuromorphic computing integration.

Tests adapter functionality without requiring actual SpikingJelly installation.
"""

import pytest

from penin.integrations.base import IntegrationStatus
from penin.integrations.neuromorphic.spikingjelly_adapter import (
    SpikingJellyConfig,
    SpikingNetworkAdapter,
)


class TestSpikingJellyAdapter:
    """Test suite for SpikingJelly adapter"""

    def test_config_creation(self):
        """Test SpikingJelly configuration creation with defaults"""
        config = SpikingJellyConfig()

        assert config.backend in ["torch", "cupy"]
        assert config.neuron_type in ["IF", "LIF", "PLIF"]
        assert config.surrogate_function in ["ATan", "Sigmoid", "Rectangle"]
        assert 1 <= config.time_steps <= 32
        assert 0.0 <= config.target_sparsity <= 1.0

    def test_config_custom_values(self):
        """Test SpikingJelly configuration with custom values"""
        config = SpikingJellyConfig(
            backend="torch",
            neuron_type="LIF",
            time_steps=8,
            target_sparsity=0.75,
            enable_cuda_enhanced=False,
        )

        assert config.backend == "torch"
        assert config.neuron_type == "LIF"
        assert config.time_steps == 8
        assert config.target_sparsity == 0.75
        assert config.enable_cuda_enhanced is False

    def test_adapter_initialization_without_spikingjelly(self):
        """Test adapter behavior when SpikingJelly is not installed"""
        adapter = SpikingNetworkAdapter()

        # Without SpikingJelly installed, is_available should return False
        available = adapter.is_available()

        # Initialization should handle missing dependency gracefully
        if not available:
            result = adapter.initialize()
            assert result is False
            assert adapter.status == IntegrationStatus.NOT_INSTALLED

    def test_adapter_get_status(self):
        """Test status reporting"""
        adapter = SpikingNetworkAdapter()

        status = adapter.get_status()

        assert "adapter" in status
        assert status["adapter"] == "SpikingJelly Neuromorphic"
        assert "status" in status
        assert "available" in status
        assert "backend" in status
        assert "neuron_type" in status
        assert "time_steps" in status
        assert "target_sparsity" in status

    @pytest.mark.asyncio
    async def test_execute_without_initialization_fails(self):
        """Test that execution fails if adapter not initialized"""
        adapter = SpikingNetworkAdapter()

        from penin.integrations.base import IntegrationExecutionError

        with pytest.raises(IntegrationExecutionError):
            await adapter.execute("convert", model=None)

    @pytest.mark.asyncio
    async def test_convert_placeholder(self):
        """Test ANN→SNN conversion structure"""
        adapter = SpikingNetworkAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        result = await adapter.execute("convert", model={"test": "ann"})

        assert "conversion_id" in result
        assert "neuron_type" in result
        assert "time_steps" in result
        assert "estimated_sparsity" in result
        assert "estimated_speedup" in result

    @pytest.mark.asyncio
    async def test_train_placeholder(self):
        """Test SNN training structure"""
        adapter = SpikingNetworkAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        result = await adapter.execute("train", model={"test": "snn"}, data={"train": "data"})

        assert "training_id" in result
        assert "final_accuracy" in result
        assert "speedup_vs_ann" in result
        assert "avg_sparsity" in result
        assert "energy_consumption" in result

    @pytest.mark.asyncio
    async def test_infer_placeholder(self):
        """Test SNN inference structure"""
        adapter = SpikingNetworkAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        result = await adapter.execute("infer", model={"test": "snn"}, data={"input": "data"})

        assert "inference_id" in result
        assert "latency_ms" in result
        assert "sparsity_achieved" in result
        assert "energy_ratio" in result
        # Energy ratio should be <<1 (much more efficient than ANN)
        assert result["energy_ratio"] < 0.5

    @pytest.mark.asyncio
    async def test_analyze_sparsity_placeholder(self):
        """Test sparsity analysis structure"""
        adapter = SpikingNetworkAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        result = await adapter.execute("analyze", model={"test": "snn"}, data={"input": "data"})

        assert "analysis_id" in result
        assert "overall_sparsity" in result
        assert "energy_efficiency" in result
        assert "speedup_potential" in result

    @pytest.mark.asyncio
    async def test_high_level_convert_interface(self):
        """Test high-level convert() method"""
        adapter = SpikingNetworkAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        pytorch_model = {"layers": ["conv1", "fc1"]}
        snn_model = await adapter.convert(pytorch_model)

        # Should return result from conversion
        # (placeholder returns None for snn_model field)
        assert snn_model is None or isinstance(snn_model, dict)

    @pytest.mark.asyncio
    async def test_fail_open_mode(self):
        """Test fail-open behavior on errors"""
        config = SpikingJellyConfig(fail_open=True)
        adapter = SpikingNetworkAdapter(config=config)
        adapter._initialized = True

        # Trigger error with invalid operation
        result = await adapter.execute("invalid_operation", None, None)

        # Should return fallback instead of raising
        assert result.get("status") == "failed"
        assert result.get("fallback") is True

    def test_cuda_enhanced_speedup(self):
        """Test that CUDA-enhanced mode promises speedup"""
        config_cuda = SpikingJellyConfig(backend="cupy", enable_cuda_enhanced=True)
        adapter = SpikingNetworkAdapter(config=config_cuda)

        # Mock initialization
        adapter._initialized = True

        # Check that CUDA enhancement is reflected in status
        status = adapter.get_status()
        assert status["cuda_enhanced"] is True

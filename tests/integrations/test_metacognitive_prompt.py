"""
Tests for Metacognitive-Prompting integration.

Tests adapter functionality for structured metacognitive reasoning.
"""

import pytest

from penin.integrations.base import IntegrationStatus
from penin.integrations.metacognition.metacognitive_prompt import (
    MetacognitivePromptConfig,
    MetacognitiveReasoner,
    MetacognitiveStage,
)


class TestMetacognitivePromptAdapter:
    """Test suite for Metacognitive-Prompting adapter"""

    def test_config_creation(self):
        """Test Metacognitive configuration creation with defaults"""
        config = MetacognitivePromptConfig()

        assert config.enable_all_stages is True
        assert config.custom_stages is None
        assert 1 <= config.reasoning_depth <= 5
        assert config.enable_self_critique is True
        assert config.enable_confidence_calibration is True

    def test_config_custom_stages(self):
        """Test configuration with custom subset of stages"""
        config = MetacognitivePromptConfig(
            custom_stages=[MetacognitiveStage.UNDERSTANDING, MetacognitiveStage.DECISION],
            reasoning_depth=3,
        )

        assert len(config.custom_stages) == 2
        assert MetacognitiveStage.UNDERSTANDING in config.custom_stages
        assert MetacognitiveStage.DECISION in config.custom_stages
        assert config.reasoning_depth == 3

    def test_metacognitive_stage_enum(self):
        """Test MetacognitiveStage enum values"""
        assert MetacognitiveStage.UNDERSTANDING.value == "understanding"
        assert MetacognitiveStage.JUDGMENT.value == "judgment"
        assert MetacognitiveStage.EVALUATION.value == "evaluation"
        assert MetacognitiveStage.DECISION.value == "decision"
        assert MetacognitiveStage.CONFIDENCE.value == "confidence"

    def test_adapter_is_always_available(self):
        """Test that metacognitive prompting is always available (it's a technique)"""
        adapter = MetacognitiveReasoner()

        # Should always be available (prompting technique, no dependency)
        assert adapter.is_available() is True

    def test_adapter_initialization(self):
        """Test adapter initialization"""
        adapter = MetacognitiveReasoner()

        result = adapter.initialize()

        assert result is True
        assert adapter.status == IntegrationStatus.INITIALIZED
        assert adapter._initialized is True

    def test_adapter_get_status(self):
        """Test status reporting"""
        config = MetacognitivePromptConfig(reasoning_depth=3, enable_self_critique=True)
        adapter = MetacognitiveReasoner(config=config)
        adapter.initialize()

        status = adapter.get_status()

        assert "adapter" in status
        assert status["adapter"] == "Metacognitive-Prompting"
        assert "status" in status
        assert "active_stages" in status
        assert "reasoning_depth" in status
        assert status["reasoning_depth"] == 3
        assert "self_critique_enabled" in status
        assert status["self_critique_enabled"] is True

    def test_active_stages_all(self):
        """Test getting all active stages"""
        config = MetacognitivePromptConfig(enable_all_stages=True)
        adapter = MetacognitiveReasoner(config=config)

        stages = adapter._get_active_stages()

        assert len(stages) == 5
        assert MetacognitiveStage.UNDERSTANDING in stages
        assert MetacognitiveStage.JUDGMENT in stages
        assert MetacognitiveStage.EVALUATION in stages
        assert MetacognitiveStage.DECISION in stages
        assert MetacognitiveStage.CONFIDENCE in stages

    def test_active_stages_custom(self):
        """Test getting custom subset of stages"""
        config = MetacognitivePromptConfig(
            custom_stages=[MetacognitiveStage.UNDERSTANDING, MetacognitiveStage.CONFIDENCE]
        )
        adapter = MetacognitiveReasoner(config=config)

        stages = adapter._get_active_stages()

        assert len(stages) == 2
        assert MetacognitiveStage.UNDERSTANDING in stages
        assert MetacognitiveStage.CONFIDENCE in stages

    @pytest.mark.asyncio
    async def test_execute_without_initialization_fails(self):
        """Test that execution fails if adapter not initialized"""
        adapter = MetacognitiveReasoner()

        from penin.integrations.base import IntegrationExecutionError

        with pytest.raises(IntegrationExecutionError):
            await adapter.execute("reason", prompt="test")

    @pytest.mark.asyncio
    async def test_full_reasoning_chain_placeholder(self):
        """Test full 5-stage reasoning chain structure"""
        adapter = MetacognitiveReasoner()
        adapter.initialize()

        prompt = "Should we promote this challenger model?"
        context = {"context": "Model shows 15% improvement", "constraints": "Budget limit $100"}

        result = await adapter.execute("reason", prompt=prompt, context=context)

        assert "reasoning_id" in result
        assert "prompt" in result
        assert "stages" in result
        assert "decision" in result
        assert "confidence_raw" in result
        assert "confidence_calibrated" in result
        assert 0.0 <= result["confidence_calibrated"] <= 1.0

    @pytest.mark.asyncio
    async def test_validate_decision_placeholder(self):
        """Test decision validation structure"""
        adapter = MetacognitiveReasoner()
        adapter.initialize()

        decision = "Promote the challenger model"
        context = {"risk": "low", "evidence": "strong"}

        result = await adapter.execute("validate", prompt=decision, context=context)

        assert "validation_id" in result
        assert "decision" in result
        assert "valid" in result
        assert "confidence" in result
        assert isinstance(result["valid"], bool)

    @pytest.mark.asyncio
    async def test_calibrate_confidence_placeholder(self):
        """Test confidence calibration structure"""
        config = MetacognitivePromptConfig(enable_confidence_calibration=True, temperature_scaling=True)
        adapter = MetacognitiveReasoner(config=config)
        adapter.initialize()

        result = await adapter.execute("calibrate", context={})

        assert "calibration_id" in result
        assert "method" in result
        assert result["method"] == "temperature_scaling"
        assert "params" in result
        assert "ece_before" in result
        assert "ece_after" in result
        # Calibration should improve ECE
        assert result["ece_after"] < result["ece_before"]

    @pytest.mark.asyncio
    async def test_high_level_reason_interface(self):
        """Test high-level reason() method"""
        adapter = MetacognitiveReasoner()
        adapter.initialize()

        prompt = "Evaluate this architecture mutation"
        stages = ["understanding", "judgment", "decision"]
        context = {"mutation": "add_layer", "expected_gain": 0.10}

        result = await adapter.reason(prompt, stages=stages, context=context)

        assert "reasoning_id" in result
        assert "decision" in result
        assert "confidence_calibrated" in result

    def test_confidence_calibration_application(self):
        """Test confidence calibration math"""
        config = MetacognitivePromptConfig(enable_confidence_calibration=True)
        adapter = MetacognitiveReasoner(config=config)
        adapter.initialize()

        # Test calibration on raw confidence
        raw_confidence = 0.9
        calibrated = adapter._apply_calibration(raw_confidence)

        # Calibrated should still be in [0, 1]
        assert 0.0 <= calibrated <= 1.0

        # With T=1.0 (default), calibration should be close to raw
        # (but not exactly due to logit transform)
        assert abs(calibrated - raw_confidence) < 0.2

    def test_confidence_calibration_disabled(self):
        """Test that calibration can be disabled"""
        config = MetacognitivePromptConfig(enable_confidence_calibration=False)
        adapter = MetacognitiveReasoner(config=config)
        adapter.initialize()

        raw_confidence = 0.75
        calibrated = adapter._apply_calibration(raw_confidence)

        # When disabled, should return raw value
        assert calibrated == raw_confidence

    @pytest.mark.asyncio
    async def test_fail_open_mode(self):
        """Test fail-open behavior on errors"""
        config = MetacognitivePromptConfig(fail_open=True)
        adapter = MetacognitiveReasoner(config=config)
        adapter.initialize()

        # Trigger error with invalid operation
        result = await adapter.execute("invalid_operation", prompt="test")

        # Should return fallback instead of raising
        assert result.get("status") == "failed"
        assert result.get("fallback") is True
        assert result.get("confidence") == 0.0

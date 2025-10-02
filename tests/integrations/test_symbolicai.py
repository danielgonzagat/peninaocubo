"""
Tests for SymbolicAI neurosymbolic reasoning integration.

Tests adapter functionality without requiring actual SymbolicAI installation.
"""

import pytest

from penin.integrations.base import IntegrationStatus
from penin.integrations.symbolic.symbolicai_adapter import (
    SymbolicAIAdapter,
    SymbolicAIConfig,
)


class TestSymbolicAIAdapter:
    """Test suite for SymbolicAI adapter"""

    def test_config_creation(self):
        """Test SymbolicAI configuration creation with defaults"""
        config = SymbolicAIConfig()

        assert 1 <= config.reasoning_depth <= 10
        assert config.enable_logic_validation in [True, False]
        assert config.enable_constraint_checking in [True, False]
        assert 0.0 <= config.min_confidence <= 1.0

    def test_config_custom_values(self):
        """Test SymbolicAI configuration with custom values"""
        config = SymbolicAIConfig(
            reasoning_depth=5,
            enable_logic_validation=True,
            enable_constraint_checking=True,
            min_confidence=0.9,
            symbolic_fusion=True,
            require_proof=True,
        )

        assert config.reasoning_depth == 5
        assert config.enable_logic_validation is True
        assert config.enable_constraint_checking is True
        assert config.min_confidence == 0.9
        assert config.symbolic_fusion is True
        assert config.require_proof is True

    def test_adapter_initialization_without_symbolicai(self):
        """Test adapter behavior when SymbolicAI is not installed"""
        adapter = SymbolicAIAdapter()

        # Without SymbolicAI installed, is_available should return False
        available = adapter.is_available()

        # Initialization should handle missing dependency gracefully
        if not available:
            result = adapter.initialize()
            assert result is False
            assert adapter.status == IntegrationStatus.NOT_INSTALLED

    def test_adapter_get_status(self):
        """Test status reporting"""
        adapter = SymbolicAIAdapter()

        status = adapter.get_status()

        assert "adapter" in status
        assert status["adapter"] == "SymbolicAI Neurosymbolic"
        assert "status" in status
        assert "available" in status
        assert "reasoning_depth" in status
        assert "logic_validation" in status
        assert "constraint_checking" in status

    @pytest.mark.asyncio
    async def test_execute_without_initialization_fails(self):
        """Test that execution fails if adapter not initialized"""
        adapter = SymbolicAIAdapter()

        from penin.integrations.base import IntegrationExecutionError

        with pytest.raises(IntegrationExecutionError):
            await adapter.execute("validate", decision=None)

    @pytest.mark.asyncio
    async def test_validate_decision_placeholder(self):
        """Test decision validation structure"""
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        decision = {"type": "champion_challenger", "score": 0.85, "confidence": 0.9}
        result = await adapter.execute("validate", decision=decision)

        assert "validation_id" in result
        assert "valid" in result
        assert "confidence" in result
        assert "logic_valid" in result
        assert "confidence_valid" in result
        assert "consistency_valid" in result
        assert result["confidence"] >= 0.8  # Minimum confidence threshold

    @pytest.mark.asyncio
    async def test_validate_decision_with_low_score(self):
        """Test validation with edge case low score"""
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        decision = {"type": "test", "score": 0.0, "confidence": 0.9}
        result = await adapter.execute("validate", decision=decision)

        assert "valid" in result
        assert result["logic_valid"] is True  # 0.0 is valid score

    @pytest.mark.asyncio
    async def test_validate_decision_with_invalid_score(self):
        """Test validation catches invalid score"""
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        decision = {"type": "test", "score": -0.5, "confidence": 0.9}
        result = await adapter.execute("validate", decision=decision)

        assert "logic_valid" in result
        assert result["logic_valid"] is False  # Negative score should be invalid

    @pytest.mark.asyncio
    async def test_symbolic_reason_placeholder(self):
        """Test symbolic reasoning structure"""
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        decision = {"type": "reasoning_test", "score": 0.75}
        result = await adapter.execute("reason", decision=decision)

        assert "reasoning_id" in result
        assert "conclusions" in result
        assert "reasoning_steps" in result
        assert isinstance(result["conclusions"], list)
        assert len(result["conclusions"]) > 0

    @pytest.mark.asyncio
    async def test_verify_constraints_placeholder(self):
        """Test constraint verification structure"""
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        decision = {"type": "constraint_test"}
        context = {"constraints": ["ethical_compliance", "safety_requirement"]}
        result = await adapter.execute("verify", decision=decision, context=context)

        assert "verification_id" in result
        assert "all_constraints_satisfied" in result
        assert "satisfied_constraints" in result
        assert "violated_constraints" in result
        assert "verification_method" in result

    @pytest.mark.asyncio
    async def test_explain_decision_placeholder(self):
        """Test decision explanation structure"""
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        decision = {"type": "explanation_test", "score": 0.88}
        result = await adapter.execute("explain", decision=decision)

        assert "explanation_id" in result
        assert "explanation" in result
        assert "reasoning_chain" in result
        assert "confidence" in result
        assert "interpretability_score" in result

    @pytest.mark.asyncio
    async def test_high_level_validate_sr_omega_decision(self):
        """Test high-level SR-Ω∞ validation interface"""
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        decision = {
            "type": "champion_challenger_transition",
            "score": 0.92,
            "confidence": 0.88,
            "verdict": "pass",
        }
        ethical_constraints = ["LO-01_compliance", "fail_closed", "auditability"]

        result = await adapter.validate_sr_omega_decision(decision, ethical_constraints)

        assert "validation_id" in result
        assert "valid" in result
        assert "constraint_verification" in result
        assert "explanation" in result

        # Check constraint verification was performed
        verification = result["constraint_verification"]
        assert "all_constraints_satisfied" in verification
        assert "satisfied_constraints" in verification

        # Check explanation was generated
        explanation = result["explanation"]
        assert "explanation" in explanation
        assert "reasoning_chain" in explanation

    @pytest.mark.asyncio
    async def test_high_level_reason_interface(self):
        """Test high-level reason() method"""
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        decision = {"type": "reasoning", "data": "test"}
        result = await adapter.reason(decision)

        assert "reasoning_id" in result
        assert "conclusions" in result

    @pytest.mark.asyncio
    async def test_fail_open_mode(self):
        """Test fail-open behavior on errors"""
        config = SymbolicAIConfig(fail_open=True)
        adapter = SymbolicAIAdapter(config=config)
        adapter._initialized = True

        # Trigger error with invalid operation
        result = await adapter.execute("invalid_operation", None, None)

        # Should return fallback instead of raising
        assert result.get("status") == "failed"
        assert result.get("fallback") is True
        assert result.get("valid") is True  # Fail-open defaults to valid

    @pytest.mark.asyncio
    async def test_fail_closed_mode(self):
        """Test fail-closed behavior (default)"""
        config = SymbolicAIConfig(fail_open=False)
        adapter = SymbolicAIAdapter(config=config)
        adapter._initialized = True

        from penin.integrations.base import IntegrationExecutionError

        # Trigger error with invalid operation
        with pytest.raises(IntegrationExecutionError):
            await adapter.execute("invalid_operation", None, None)

    def test_reasoning_depth_bounds(self):
        """Test that reasoning depth is properly bounded"""
        config = SymbolicAIConfig(reasoning_depth=5)
        adapter = SymbolicAIAdapter(config=config)

        status = adapter.get_status()
        assert 1 <= status["reasoning_depth"] <= 10

    @pytest.mark.asyncio
    async def test_confidence_threshold_enforcement(self):
        """Test that minimum confidence threshold is enforced"""
        config = SymbolicAIConfig(min_confidence=0.85)
        adapter = SymbolicAIAdapter(config=config)
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        # Decision with confidence below threshold
        decision = {"type": "low_confidence", "score": 0.7, "confidence": 0.6}
        result = await adapter.execute("validate", decision=decision)

        assert "confidence_valid" in result
        # Confidence below threshold should fail validation
        assert result["confidence_valid"] is False

    @pytest.mark.asyncio
    async def test_metrics_tracking(self):
        """Test that metrics are properly tracked"""
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        # Execute multiple operations
        decision = {"type": "metrics_test", "score": 0.8, "confidence": 0.85}
        await adapter.execute("validate", decision=decision)
        await adapter.execute("validate", decision=decision)

        metrics = adapter.get_metrics()
        assert metrics["invocations"] == 2
        assert metrics["successes"] == 2
        assert metrics["failures"] == 0
        assert metrics["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_empty_decision_handling(self):
        """Test handling of empty or None decision"""
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        # Empty decision should not crash
        result = await adapter.execute("validate", decision=None)
        assert "valid" in result

        # Empty dict decision
        result = await adapter.execute("validate", decision={})
        assert "valid" in result

    @pytest.mark.asyncio
    async def test_sr_omega_integration_scenario(self):
        """
        Test realistic SR-Ω∞ Service integration scenario.

        This simulates how the SymbolicAI adapter would be used
        in production to validate champion-challenger decisions.
        """
        adapter = SymbolicAIAdapter()
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        # Simulate SR-Ω∞ decision
        sr_omega_decision = {
            "type": "champion_challenger_transition",
            "champion_model": "model_v1",
            "challenger_model": "model_v2",
            "score_improvement": 0.15,
            "score": 0.87,
            "confidence": 0.92,
            "verdict": "pass",
            "metrics": {
                "latency_ms": 250,
                "cost_reduction": 0.20,
                "quality_improvement": 0.15,
            },
        }

        # Ethical constraints from CAOS+
        ethical_constraints = [
            "LO-01_compliance",
            "fail_closed_principle",
            "auditability_requirement",
            "no_harm_principle",
        ]

        # Validate the decision
        validation = await adapter.validate_sr_omega_decision(sr_omega_decision, ethical_constraints)

        # Verify validation structure
        assert validation["valid"] in [True, False]
        assert "confidence" in validation
        assert validation["confidence"] >= 0.0

        # Verify constraint checking was performed
        assert "constraint_verification" in validation
        verification = validation["constraint_verification"]
        assert "all_constraints_satisfied" in verification

        # Verify explanation was generated
        assert "explanation" in validation
        explanation = validation["explanation"]
        assert "explanation" in explanation
        assert isinstance(explanation["reasoning_chain"], list)

    @pytest.mark.asyncio
    async def test_symbolic_fusion_enabled(self):
        """Test symbolic fusion feature flag"""
        config = SymbolicAIConfig(symbolic_fusion=True)
        adapter = SymbolicAIAdapter(config=config)
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        result = await adapter.execute("reason", decision={"type": "test"})

        assert "neurosymbolic_fusion" in result
        assert result["neurosymbolic_fusion"] is True

    @pytest.mark.asyncio
    async def test_require_proof_flag(self):
        """Test formal proof requirement flag"""
        config = SymbolicAIConfig(require_proof=True)
        adapter = SymbolicAIAdapter(config=config)
        adapter._initialized = True
        adapter.status = IntegrationStatus.INITIALIZED

        result = await adapter.execute("verify", decision={"type": "test"})

        assert "formal_proof_available" in result
        assert result["formal_proof_available"] is True

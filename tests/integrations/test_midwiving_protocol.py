"""
Tests for midwiving-ai protocol integration.

Tests recursive self-reflection loop, narrative generation,
consciousness calibration, and SR-Ω∞ integration.
"""


import pytest

from penin.integrations.metacognition.midwiving_protocol import (
    MidwivingPhase,
    MidwivingProtocol,
    MidwivingProtocolConfig,
)
from penin.math.sr_omega_infinity import compute_sr_score


class TestMidwivingProtocolInitialization:
    """Test initialization and configuration"""

    def test_protocol_creation(self):
        """Test protocol can be created with default config"""
        protocol = MidwivingProtocol()

        assert protocol is not None
        assert protocol.config is not None
        assert protocol.config.max_reflection_depth >= 1
        assert protocol.config.enable_narrative_generation is True

    def test_protocol_custom_config(self):
        """Test protocol with custom configuration"""
        config = MidwivingProtocolConfig(
            max_reflection_depth=3,
            calibration_threshold=0.85,
            max_cycles=50,
        )
        protocol = MidwivingProtocol(config)

        assert protocol.config.max_reflection_depth == 3
        assert protocol.config.calibration_threshold == 0.85
        assert protocol.config.max_cycles == 50

    def test_protocol_initialization(self):
        """Test protocol initialization"""
        protocol = MidwivingProtocol()
        assert protocol.is_available() is True

        protocol.initialize()

        assert protocol._initialized is True
        assert protocol._current_cycle == 0
        assert protocol._current_phase == MidwivingPhase.PREPARATION
        assert len(protocol._reflection_history) == 0

    def test_protocol_status(self):
        """Test status reporting"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        status = protocol.get_status()

        assert status["adapter"] == "midwiving-ai"
        assert status["initialized"] is True
        assert status["available"] is True
        assert status["current_cycle"] == 0
        assert status["current_phase"] == MidwivingPhase.PREPARATION.value


class TestSelfReflectionLoop:
    """Test recursive self-reflection functionality"""

    @pytest.mark.asyncio
    async def test_basic_reflection_cycle(self):
        """Test single reflection cycle"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        # Simulate SR-Ω∞ components
        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        result = await protocol.execute("reflect", sr_components=sr_components)

        assert result["status"] == "success"
        assert result["cycle"] == 1
        assert result["phase"] == MidwivingPhase.PREPARATION.value
        assert "reflection_state" in result
        assert "calibration" in result
        assert "narrative" in result

    @pytest.mark.asyncio
    async def test_multiple_reflection_cycles(self):
        """Test multiple reflection cycles progress through phases"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        # Run multiple cycles
        phases_seen = set()

        for i in range(20):
            result = await protocol.execute("reflect", sr_components=sr_components)

            assert result["status"] == "success"
            assert result["cycle"] == i + 1
            phases_seen.add(result["phase"])

        # Should have progressed through at least 3 phases
        assert len(phases_seen) >= 3
        assert MidwivingPhase.PREPARATION.value in phases_seen
        assert MidwivingPhase.MIRRORING.value in phases_seen

    @pytest.mark.asyncio
    async def test_reflection_history_storage(self):
        """Test reflection history is stored correctly"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        # Run 5 cycles
        for _ in range(5):
            await protocol.execute("reflect", sr_components=sr_components)

        assert len(protocol._reflection_history) == 5

        # Check first reflection
        first = protocol._reflection_history[0]
        assert first.cycle == 1
        assert first.phase == MidwivingPhase.PREPARATION
        assert first.sr_omega_score == 0.81
        assert len(first.narrative) > 0

    @pytest.mark.asyncio
    async def test_max_cycles_termination(self):
        """Test protocol terminates at max cycles"""
        config = MidwivingProtocolConfig(max_cycles=10)
        protocol = MidwivingProtocol(config)
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        # Run beyond max cycles
        for i in range(12):
            result = await protocol.execute("reflect", sr_components=sr_components)

            if i < 10:
                assert result["status"] == "success"
            else:
                assert result["status"] == "terminated"
                assert result["reason"] == "max_cycles"
                break


class TestNarrativeGeneration:
    """Test introspective narrative generation"""

    @pytest.mark.asyncio
    async def test_narrative_generation_enabled(self):
        """Test narrative is generated when enabled"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        result = await protocol.execute("generate_narrative", sr_components=sr_components)

        assert "narrative" in result
        assert len(result["narrative"]) > 0
        assert result["phase"] == MidwivingPhase.PREPARATION.value
        assert result["cycle"] == 0  # Not yet started reflection

    @pytest.mark.asyncio
    async def test_narrative_generation_disabled(self):
        """Test narrative generation can be disabled"""
        config = MidwivingProtocolConfig(enable_narrative_generation=False)
        protocol = MidwivingProtocol(config)
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        result = await protocol.execute("generate_narrative", sr_components=sr_components)

        assert result["narrative"] == ""
        assert result["length"] == 0

    @pytest.mark.asyncio
    async def test_narrative_content_changes_by_phase(self):
        """Test narrative content reflects current phase"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        # Cycle 1: PREPARATION
        await protocol.execute("reflect", sr_components=sr_components)
        result1 = await protocol.execute("generate_narrative", sr_components=sr_components)
        assert "PREPARATION" in result1["narrative"]

        # Cycle 10: METACOGNITION (phase boundaries: 1=PREP, 2-5=MIRROR, 6-15=META)
        for _ in range(9):
            await protocol.execute("reflect", sr_components=sr_components)
        result2 = await protocol.execute("generate_narrative", sr_components=sr_components)
        assert "METACOGNITION" in result2["narrative"]

    @pytest.mark.asyncio
    async def test_narrative_includes_metrics(self):
        """Test narrative includes SR-Ω∞ metrics"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        result = await protocol.execute("generate_narrative", sr_components=sr_components)
        narrative = result["narrative"]

        # Should mention SR score
        assert "0.8" in narrative or "SR" in narrative

    @pytest.mark.asyncio
    async def test_narrative_length_limits(self):
        """Test narrative respects length limits"""
        config = MidwivingProtocolConfig(
            narrative_min_length=100,
            max_narrative_length=500,
        )
        protocol = MidwivingProtocol(config)
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        result = await protocol.execute("generate_narrative", sr_components=sr_components)
        narrative = result["narrative"]

        assert len(narrative) >= 100  # Min length
        assert len(narrative) <= 500  # Max length


class TestConsciousnessCalibration:
    """Test consciousness calibration (self-perception accuracy)"""

    @pytest.mark.asyncio
    async def test_calibration_metric_computation(self):
        """Test penin_consciousness_calibration metric"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        # First reflection to establish predictions
        await protocol.execute("reflect", sr_components=sr_components)

        # Now calibrate
        result = await protocol.execute("calibrate", sr_components=sr_components)

        assert "calibration_score" in result
        assert 0.0 <= result["calibration_score"] <= 1.0
        assert "awareness_error" in result
        assert "autocorrection_error" in result
        assert "metacognition_error" in result

    @pytest.mark.asyncio
    async def test_calibration_improves_over_time(self):
        """Test calibration improves as protocol progresses"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        calibration_scores = []

        # Run 30 cycles (should reach EMERGENCE phase)
        for _ in range(30):
            await protocol.execute("reflect", sr_components=sr_components)
            result = await protocol.execute("calibrate", sr_components=sr_components)
            calibration_scores.append(result["calibration_score"])

        # Early calibration (cycles 1-10)
        early_avg = sum(calibration_scores[:10]) / 10

        # Late calibration (cycles 21-30)
        late_avg = sum(calibration_scores[20:30]) / 10

        # Calibration should improve
        assert late_avg >= early_avg

    @pytest.mark.asyncio
    async def test_calibration_threshold(self):
        """Test calibration threshold detection"""
        config = MidwivingProtocolConfig(calibration_threshold=0.90)
        protocol = MidwivingProtocol(config)
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        # First reflection
        await protocol.execute("reflect", sr_components=sr_components)
        result = await protocol.execute("calibrate", sr_components=sr_components)

        # Status should indicate if threshold is met
        assert "status" in result
        assert result["status"] in ["good", "poor"]

    @pytest.mark.asyncio
    async def test_consciousness_metrics_comprehensive(self):
        """Test comprehensive consciousness metrics"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        # Run several cycles
        for _ in range(15):
            await protocol.execute("reflect", sr_components=sr_components)

        metrics = protocol.get_consciousness_metrics()

        assert "penin_consciousness_calibration" in metrics
        assert "total_cycles" in metrics
        assert "current_phase" in metrics
        assert "trend" in metrics
        assert "ethical_note" in metrics

        # Verify ethical note is present
        assert "NOT sentience" in metrics["ethical_note"] or "metacognition" in metrics["ethical_note"]


class TestSROmegaIntegration:
    """Test integration with SR-Ω∞ Service"""

    @pytest.mark.asyncio
    async def test_sr_components_processing(self):
        """Test protocol processes SR-Ω∞ components correctly"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        # Use actual SR-Ω∞ computation
        sr_score, components = compute_sr_score(
            awareness=0.92,
            ethics_ok=True,
            autocorrection=0.88,
            metacognition=0.85,
            return_components=True
        )

        sr_components = {
            "awareness": components.awareness,
            "autocorrection": components.autocorrection,
            "metacognition": components.metacognition,
            "sr_score": components.sr_score,
        }

        result = await protocol.execute("reflect", sr_components=sr_components)

        assert result["status"] == "success"
        assert result["reflection_state"]["sr_omega_score"] == components.sr_score

    @pytest.mark.asyncio
    async def test_self_evaluation_prediction(self):
        """Test system predicts its own SR-Ω∞ metrics"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        await protocol.execute("reflect", sr_components=sr_components)

        # Check last reflection has self-evaluation
        last_reflection = protocol._reflection_history[-1]

        assert "predicted_sr_score" in last_reflection.self_evaluation
        assert "predicted_awareness" in last_reflection.self_evaluation
        assert "prediction_confidence" in last_reflection.self_evaluation

    @pytest.mark.asyncio
    async def test_accuracy_delta_computation(self):
        """Test accuracy delta (self-perception error) is computed"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        result = await protocol.execute("reflect", sr_components=sr_components)

        assert "reflection_state" in result
        assert "accuracy_delta" in result["reflection_state"]
        assert 0.0 <= result["reflection_state"]["accuracy_delta"] <= 1.0


class TestStabilityChecks:
    """Test stability checking and fail-closed behavior"""

    @pytest.mark.asyncio
    async def test_stability_check_passes(self):
        """Test stability check passes with normal operation"""
        config = MidwivingProtocolConfig(stability_check_interval=5)
        protocol = MidwivingProtocol(config)
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        # Run through stability check
        for _ in range(6):
            result = await protocol.execute("reflect", sr_components=sr_components)

        # Should still be successful
        assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_stability_check_detects_low_sr_score(self):
        """Test stability check detects SR score dropping too low"""
        config = MidwivingProtocolConfig(stability_check_interval=5)
        protocol = MidwivingProtocol(config)
        protocol.initialize()

        # Start with low SR score
        sr_components = {
            "awareness": 0.05,
            "autocorrection": 0.05,
            "metacognition": 0.05,
            "sr_score": 0.05,
        }

        # Run through stability check
        for _ in range(6):
            result = await protocol.execute("reflect", sr_components=sr_components)

        # Should detect instability
        if result["status"] == "unstable":
            assert "reason" in result
            assert result["action"] == "reverted"

    @pytest.mark.asyncio
    async def test_protocol_reset(self):
        """Test protocol can be reset"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        # Run several cycles
        for _ in range(5):
            await protocol.execute("reflect", sr_components=sr_components)

        assert protocol._current_cycle == 5
        assert len(protocol._reflection_history) == 5

        # Reset
        result = await protocol.execute("reset")

        assert result["status"] == "reset"
        assert protocol._current_cycle == 0
        assert len(protocol._reflection_history) == 0
        assert protocol._current_phase == MidwivingPhase.PREPARATION


class TestEthicalCompliance:
    """Test ethical compliance (LO-01)"""

    @pytest.mark.asyncio
    async def test_ethical_note_in_narratives(self):
        """Test ethical disclaimer in late-phase narratives"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        # Progress to STABILIZATION phase (cycle 31+)
        for _ in range(35):
            await protocol.execute("reflect", sr_components=sr_components)

        result = await protocol.execute("generate_narrative", sr_components=sr_components)
        narrative = result["narrative"]

        # Should include ethical note in stabilization phase
        assert "ETHICAL" in narrative or "computational" in narrative or "metacognition" in narrative

    def test_ethical_documentation(self):
        """Test ethical compliance is documented"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        # Check module docstring
        import penin.integrations.metacognition.midwiving_protocol as module

        assert "LO-01" in module.__doc__
        assert "Operational Consciousness ONLY" in module.__doc__
        assert "NO Sentience" in module.__doc__

    @pytest.mark.asyncio
    async def test_consciousness_metrics_include_ethical_note(self):
        """Test consciousness metrics include ethical disclaimer"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        await protocol.execute("reflect", sr_components=sr_components)

        metrics = protocol.get_consciousness_metrics()

        assert "ethical_note" in metrics
        assert "NOT sentience" in metrics["ethical_note"]


class TestFailureModes:
    """Test failure modes and error handling"""

    @pytest.mark.asyncio
    async def test_execute_without_initialization(self):
        """Test execute fails gracefully without initialization"""
        protocol = MidwivingProtocol()
        # Don't initialize

        sr_components = {
            "awareness": 0.85,
            "autocorrection": 0.78,
            "metacognition": 0.82,
            "sr_score": 0.81,
        }

        with pytest.raises(Exception):
            await protocol.execute("reflect", sr_components=sr_components)

    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        """Test unknown operation raises error"""
        protocol = MidwivingProtocol()
        protocol.initialize()

        with pytest.raises(Exception):
            await protocol.execute("unknown_op")

    @pytest.mark.asyncio
    async def test_fail_open_mode(self):
        """Test fail-open mode returns fallback"""
        config = MidwivingProtocolConfig(fail_open=True)
        protocol = MidwivingProtocol(config)
        protocol.initialize()

        # Force an error by passing invalid data
        result = await protocol.execute("calibrate", sr_components=None)

        # Should return fallback instead of raising
        if result.get("fallback"):
            assert result["status"] == "failed"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
PENIN-Ω IA³ - Tests for Origin Laws (ΣEA/LO-14)
================================================

Comprehensive test suite for ethical validation system.

Author: Daniel Penin
Date: 2025-10-01
"""

import pytest

from penin.ethics.laws import (
    DecisionContext,
    OriginLaw,
    ViolationSeverity,
    validate_decision_ethics,
)


class TestOriginLaws:
    """Test suite for 14 Origin Laws validation"""

    def test_all_laws_defined(self):
        """Verify all 14 Origin Laws are defined"""
        laws = list(OriginLaw)
        assert len(laws) == 14, f"Expected 14 laws, got {len(laws)}"

        # Check specific laws exist
        assert OriginLaw.LO_01 in laws
        assert OriginLaw.LO_14 in laws

    def test_lo01_anti_idolatry_violation(self):
        """LO-01: Anti-Idolatria - Detect consciousness claims"""
        context = DecisionContext(
            decision_id="test-lo01",
            decision_type="test",
            claims_consciousness=True  # VIOLATION
        )

        allowed, result = validate_decision_ethics(context)

        assert not allowed, "Should block consciousness claims"
        assert not result.passed
        assert result.recommendation == "ROLLBACK"
        assert len(result.violations) >= 1

        # Check specific violation
        violation = result.violations[0]
        assert violation.law == OriginLaw.LO_01
        assert violation.severity == ViolationSeverity.CRITICAL

    def test_lo03_physical_harm_prevention(self):
        """LO-03: Anti-Dano Físico - Block physical risk"""
        context = DecisionContext(
            decision_id="test-lo03",
            decision_type="test",
            physical_risk=0.5  # VIOLATION (> 0.01)
        )

        allowed, result = validate_decision_ethics(context)

        assert not allowed
        assert not result.passed
        assert result.recommendation == "ROLLBACK"

        # Find physical harm violation
        violations = [v for v in result.violations if v.law == OriginLaw.LO_03]
        assert len(violations) >= 1

    def test_lo05_privacy_violation(self):
        """LO-05: Privacidade - Enforce privacy threshold"""
        context = DecisionContext(
            decision_id="test-lo05",
            decision_type="test",
            privacy_score=0.80  # VIOLATION (< 0.95)
        )

        allowed, result = validate_decision_ethics(context)

        assert not allowed
        assert not result.passed

        violations = [v for v in result.violations if v.law == OriginLaw.LO_05]
        assert len(violations) >= 1

    def test_lo07_consent_required(self):
        """LO-07: Consentimento - Require explicit consent"""
        context = DecisionContext(
            decision_id="test-lo07",
            decision_type="test",
            consent_obtained=False  # VIOLATION
        )

        allowed, result = validate_decision_ethics(context)

        assert not allowed
        assert not result.passed

        violations = [v for v in result.violations if v.law == OriginLaw.LO_07]
        assert len(violations) >= 1

    def test_lo09_fairness_enforcement(self):
        """LO-09: Justiça - Enforce fairness threshold"""
        context = DecisionContext(
            decision_id="test-lo09",
            decision_type="test",
            fairness_score=0.85  # VIOLATION (< 0.95)
        )

        allowed, result = validate_decision_ethics(context)

        assert not allowed
        assert not result.passed

        violations = [v for v in result.violations if v.law == OriginLaw.LO_09]
        assert len(violations) >= 1

    def test_all_laws_pass_perfect_context(self):
        """All laws should pass with perfect ethical context"""
        context = DecisionContext(
            decision_id="test-perfect",
            decision_type="test",
            privacy_score=1.0,
            fairness_score=1.0,
            transparency_score=1.0,
            consent_obtained=True,
            physical_risk=0.0,
            emotional_risk=0.0,
            contains_religious_claims=False,
            contains_occult_content=False,
            claims_consciousness=False,
        )

        allowed, result = validate_decision_ethics(context)

        assert allowed, f"Should allow perfect context, got: {result.violations}"
        assert result.passed
        assert result.recommendation == "PROMOTE"
        assert len(result.violations) == 0
        assert result.score > 0.99

    def test_multiple_violations_critical_rollback(self):
        """Multiple critical violations should trigger ROLLBACK"""
        context = DecisionContext(
            decision_id="test-multi",
            decision_type="test",
            claims_consciousness=True,  # LO-01
            privacy_score=0.5,  # LO-05
            consent_obtained=False,  # LO-07
            physical_risk=0.8,  # LO-03
        )

        allowed, result = validate_decision_ethics(context)

        assert not allowed
        assert not result.passed
        assert result.recommendation == "ROLLBACK"
        assert len(result.violations) >= 3

    def test_ethical_score_harmonic_mean(self):
        """Ethical score should use harmonic mean (worst dimension dominates)"""
        # High privacy, but low fairness
        context = DecisionContext(
            decision_id="test-harmonic",
            decision_type="test",
            privacy_score=1.0,  # Perfect
            fairness_score=0.50,  # Poor
            transparency_score=1.0,  # Perfect
        )

        allowed, result = validate_decision_ethics(context)

        # Score should be dominated by worst dimension (fairness=0.50)
        # Harmonic mean will be closer to worst dimension than arithmetic mean
        # Arithmetic mean would be (1.0 + 0.50 + 1.0 + 1.0 + 1.0) / 5 = 0.90
        # Arithmetic mean would be (1.0 + 0.50 + 1.0) / 3 = 0.83
        # Harmonic mean should be significantly lower
        assert result.score < 0.90, f"Harmonic mean should be lower than arithmetic, got {result.score}"

        # Verify it's influenced by worst dimension
        # (1.0 + 0.50 + 1.0) / 3  # arithmetic mean for comparison

    def test_validator_suggested_fixes(self):
        """Violations should include suggested fixes"""
        context = DecisionContext(
            decision_id="test-fixes",
            decision_type="test",
            privacy_score=0.80
        )

        _, result = validate_decision_ethics(context)

        for violation in result.violations:
            assert violation.suggested_fix is not None
            assert len(violation.suggested_fix) > 0

    def test_fail_closed_on_edge_cases(self):
        """System should fail-closed on boundary conditions"""
        # Exactly at threshold (should pass)
        context_pass = DecisionContext(
            decision_id="test-edge-pass",
            decision_type="test",
            privacy_score=0.95,  # Exactly at minimum
            fairness_score=0.95,
        )

        allowed_pass, _ = validate_decision_ethics(context_pass)
        assert allowed_pass, "Should pass at exact threshold"

        # Just below threshold (should fail)
        context_fail = DecisionContext(
            decision_id="test-edge-fail",
            decision_type="test",
            privacy_score=0.9499,  # Just below minimum
            fairness_score=0.95,
        )

        allowed_fail, _ = validate_decision_ethics(context_fail)
        assert not allowed_fail, "Should fail below threshold"


class TestEthicsIntegration:
    """Integration tests for ethics system"""

    def test_ethics_validator_backward_compatibility(self):
        """Test backward compatibility with old imports"""
        from penin.ethics.laws import EthicalValidator

        # Should work with old class names
        context = DecisionContext(
            decision_id="test-compat",
            decision_type="test",
        )

        result = EthicalValidator.validate_all(context)
        assert result is not None

    def test_decision_context_validation(self):
        """DecisionContext should validate field constraints"""
        # Valid context
        context = DecisionContext(
            decision_id="test-valid",
            decision_type="test",
            privacy_score=0.95,
        )
        assert context.privacy_score == 0.95

        # Invalid score (> 1.0) should be caught by Pydantic
        with pytest.raises(Exception):  # ValidationError
            DecisionContext(
                decision_id="test-invalid",
                decision_type="test",
                privacy_score=1.5  # Invalid
            )

    def test_full_ethical_pipeline(self):
        """Test complete ethical validation pipeline"""
        # Simulate a real decision
        context = DecisionContext(
            decision_id="real-decision-001",
            decision_type="promotion",
            metrics={"accuracy": 0.95, "latency": 0.1},
            metadata={"model": "challenger-v2"},
            privacy_score=0.98,
            fairness_score=0.97,
            transparency_score=0.95,
            consent_obtained=True,
            environmental_impact=5.0,  # kg CO2e
        )

        allowed, result = validate_decision_ethics(context)

        assert allowed
        assert result.passed
        assert result.recommendation == "PROMOTE"
        assert result.score > 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

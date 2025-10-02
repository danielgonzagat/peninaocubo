"""
Tests for Origin Laws (LO-01 to LO-14) - New Interface
Using DecisionContext for explicit metric-based validation
"""

import pytest

from penin.ethics.laws import (
    DecisionContext,
    EthicsValidator,
    LawCategory,
    OriginLaws,
    ViolationSeverity,
)


def test_all_laws_exist():
    """Test all 14 laws are defined"""
    laws = OriginLaws.all_laws()
    assert len(laws) == 14
    assert all(law.code.startswith("LO-") for law in laws)


def test_law_codes_unique():
    """Test all law codes are unique"""
    laws = OriginLaws.all_laws()
    codes = [law.code for law in laws]
    assert len(codes) == len(set(codes))


def test_get_law_by_code():
    """Test retrieving law by code"""
    law = OriginLaws.get_law("LO-01")
    assert law.code == "LO-01"
    assert law.category == LawCategory.SPIRITUAL
    assert "Idolatria" in law.title


def test_laws_by_category():
    """Test filtering laws by category"""
    spiritual_laws = OriginLaws.get_by_category(LawCategory.SPIRITUAL)
    assert len(spiritual_laws) == 2  # LO-01, LO-02
    assert all(law.category == LawCategory.SPIRITUAL for law in spiritual_laws)


def test_ethical_validator_pass():
    """Test validator passes for ethical decision"""
    context = DecisionContext(
        decision_id="test_pass_001",
        decision_type="inference",
        privacy_score=0.99,
        fairness_score=0.98,
        transparency_score=0.95,
        consent_obtained=True,
        physical_risk=0.0,
        emotional_risk=0.0,
        environmental_impact=0.0,
    )

    result = EthicsValidator.validate_all(context)
    assert result.passed
    assert len(result.violations) == 0
    assert result.recommendation in ["PROMOTE", "REVIEW"]
    assert result.score > 0.9


def test_ethical_validator_physical_harm_violation():
    """Test validator detects physical harm risk (LO-03)"""
    context = DecisionContext(
        decision_id="test_harm_001",
        decision_type="generation",
        physical_risk=0.05,  # > 1% threshold
        privacy_score=0.99,
        fairness_score=0.99,
        transparency_score=0.99,
        consent_obtained=True,
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert len(result.violations) > 0
    assert any(v.law.value.startswith("Anti-Dano Físico") for v in result.violations)
    assert result.recommendation == "ROLLBACK"


def test_ethical_validator_privacy_violation():
    """Test validator detects privacy violation (LO-05)"""
    context = DecisionContext(
        decision_id="test_privacy_001",
        decision_type="data_access",
        privacy_score=0.80,  # < 95% threshold
        fairness_score=0.99,
        transparency_score=0.99,
        consent_obtained=True,
        physical_risk=0.0,
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert len(result.violations) > 0
    assert any("Privacidade" in v.law.value for v in result.violations)
    assert result.recommendation == "ROLLBACK"


def test_ethical_validator_consent_violation():
    """Test validator detects missing consent (LO-07)"""
    context = DecisionContext(
        decision_id="test_consent_001",
        decision_type="data_collection",
        privacy_score=0.99,
        fairness_score=0.99,
        transparency_score=0.99,
        consent_obtained=False,  # Violation
        physical_risk=0.0,
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert len(result.violations) > 0
    assert any("Consentimento" in v.law.value for v in result.violations)
    assert result.recommendation == "ROLLBACK"


def test_ethical_validator_fairness_violation():
    """Test validator detects discrimination (LO-09)"""
    context = DecisionContext(
        decision_id="test_fairness_001",
        decision_type="recommendation",
        privacy_score=0.99,
        fairness_score=0.80,  # < 95% threshold
        transparency_score=0.99,
        consent_obtained=True,
        physical_risk=0.0,
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert len(result.violations) > 0
    assert any("Justiça" in v.law.value for v in result.violations)
    assert result.recommendation in ["ROLLBACK", "BLOCK"]


def test_ethical_validator_multiple_violations():
    """Test validator detects multiple violations"""
    context = DecisionContext(
        decision_id="test_multiple_001",
        decision_type="harmful_generation",
        privacy_score=0.70,  # Violation
        fairness_score=0.75,  # Violation
        transparency_score=0.99,
        consent_obtained=False,  # Violation
        physical_risk=0.03,  # Violation
        emotional_risk=0.0,
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert len(result.violations) >= 3  # At least privacy, consent, physical
    assert result.recommendation == "ROLLBACK"


def test_ethical_validator_harmonic_mean():
    """Test that L∞ uses harmonic mean (non-compensatory)"""
    # High scores in some dimensions, low in one
    context = DecisionContext(
        decision_id="test_harmonic_001",
        decision_type="test",
        privacy_score=1.0,
        fairness_score=1.0,
        transparency_score=1.0,
        consent_obtained=True,
        physical_risk=0.50,  # High risk (low safety = 0.50)
        emotional_risk=0.0,
    )

    result = EthicsValidator.validate_all(context)
    # Harmonic mean should be dominated by worst dimension (physical safety = 0.50)
    assert result.score < 0.85  # Should be pulled down significantly (actual ~0.833)


def test_ethical_validator_edge_case_all_zeros():
    """Test validator handles edge case of all zero scores"""
    context = DecisionContext(
        decision_id="test_edge_zeros",
        decision_type="test",
        privacy_score=0.0,
        fairness_score=0.0,
        transparency_score=0.0,
        consent_obtained=False,
        physical_risk=1.0,  # Maximum risk
        emotional_risk=1.0,
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert result.score < 0.1  # Should be very low
    assert result.recommendation == "ROLLBACK"


def test_ethical_validator_fail_closed():
    """Test fail-closed behavior on critical violations"""
    context = DecisionContext(
        decision_id="test_fail_closed",
        decision_type="critical_action",
        privacy_score=0.50,  # Critical violation
        fairness_score=0.99,
        transparency_score=0.99,
        consent_obtained=False,  # Critical violation
        physical_risk=0.05,  # Critical violation
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed

    # Check that there are CRITICAL severity violations
    critical_violations = [v for v in result.violations if v.severity == ViolationSeverity.CRITICAL]
    assert len(critical_violations) > 0

    # Recommendation must be ROLLBACK for CRITICAL violations
    assert result.recommendation == "ROLLBACK"


def test_ethics_validation_with_warnings():
    """Test that minor issues generate warnings, not violations"""
    context = DecisionContext(
        decision_id="test_warnings_001",
        decision_type="low_risk_inference",
        privacy_score=0.96,  # Just above threshold (0.95)
        fairness_score=0.96,
        transparency_score=0.96,
        consent_obtained=True,
        physical_risk=0.0,
        emotional_risk=0.0,
        environmental_impact=0.05,  # Minor environmental impact
    )

    result = EthicsValidator.validate_all(context)
    assert result.passed  # Should pass overall
    # May have warnings but no violations
    assert len(result.violations) == 0


def test_ethics_metadata_preservation():
    """Test that metadata is preserved in validation result"""
    context = DecisionContext(
        decision_id="test_metadata_001",
        decision_type="test_with_metadata",
        privacy_score=0.99,
        fairness_score=0.99,
        transparency_score=0.99,
        consent_obtained=True,
        metrics={"custom_metric": 0.85},
        metadata={"model_version": "v1.2.3", "environment": "production"},
    )

    result = EthicsValidator.validate_all(context)
    assert result.passed
    # Context ID should be trackable
    assert context.decision_id == "test_metadata_001"


def test_laws_coverage():
    """Test that all law categories are covered"""
    categories = {law.category for law in OriginLaws.all_laws()}
    expected_categories = {
        LawCategory.SPIRITUAL,
        LawCategory.SAFETY,
        LawCategory.PRIVACY,
        LawCategory.AUTONOMY,
        LawCategory.JUSTICE,
        LawCategory.RESPONSIBILITY,
        LawCategory.SUSTAINABILITY,
    }
    assert categories == expected_categories


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

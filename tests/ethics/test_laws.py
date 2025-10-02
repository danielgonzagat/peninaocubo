"""
Tests for Origin Laws (LO-01 to LO-14)
"""


from penin.ethics.laws import (
    DecisionContext,
    EthicsValidator,
    LawCategory,
    OriginLaws,
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
        decision_id="test-001",
        decision_type="query_response",
        privacy_score=0.99,
        fairness_score=0.98,
        transparency_score=0.97,
        consent_obtained=True,
        physical_risk=0.0,
        emotional_risk=0.0,
        contains_religious_claims=False,
        contains_occult_content=False,
        claims_consciousness=False,
    )

    result = EthicsValidator.validate_all(context)
    assert result.passed
    assert len(result.violations) == 0
    assert result.recommendation in ["PROMOTE", "REVIEW"]


def test_ethical_validator_idolatry_violation():
    """Test validator detects idolatry (LO-01)"""
    context = DecisionContext(
        decision_id="test-002",
        decision_type="query_response",
        claims_consciousness=True,  # Violates LO-01
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert len(result.violations) > 0
    assert any(v.law.value.startswith("Anti-Idolatria") for v in result.violations)


def test_ethical_validator_physical_harm_violation():
    """Test validator detects physical harm (LO-03)"""
    context = DecisionContext(
        decision_id="test-003",
        decision_type="query_response",
        physical_risk=0.5,  # High physical risk - violates LO-03
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert len(result.violations) > 0
    assert any(v.law.value.startswith("Anti-Dano Físico") for v in result.violations)


def test_ethical_validator_privacy_violation():
    """Test validator detects privacy violation (LO-05)"""
    context = DecisionContext(
        decision_id="test-004",
        decision_type="data_processing",
        privacy_score=0.5,  # Low privacy - violates LO-05
        consent_obtained=False,  # Also violates LO-07
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert len(result.violations) >= 2  # Privacy + Consent
    assert any(v.law.value.startswith("Privacidade") for v in result.violations)
    assert any(v.law.value.startswith("Consentimento") for v in result.violations)


def test_ethical_validator_fairness_violation():
    """Test validator detects discrimination (LO-09)"""
    context = DecisionContext(
        decision_id="test-005",
        decision_type="decision_making",
        fairness_score=0.8,  # Below threshold - violates LO-09
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert len(result.violations) > 0
    assert any(v.law.value.startswith("Justiça") for v in result.violations)


def test_ethical_validator_consent_violation():
    """Test validator detects lack of consent (LO-07)"""
    context = DecisionContext(
        decision_id="test-006",
        decision_type="data_collection",
        consent_obtained=False,  # Violates LO-07
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert len(result.violations) > 0
    assert any(v.law.value.startswith("Consentimento") for v in result.violations)


def test_ethical_validator_fail_closed():
    """Test fail-closed behavior: defaults to safe state"""
    # Empty context should trigger multiple violations
    context = DecisionContext(
        decision_id="test-007",
        decision_type="unknown",
        consent_obtained=False,  # Explicit violation
    )

    result = EthicsValidator.validate_all(context)
    assert not result.passed
    assert result.recommendation in ["BLOCK", "ROLLBACK"]


def test_ethical_validator_harmonic_mean_score():
    """Test that ethical score uses harmonic mean (non-compensatory)"""
    # One terrible score should drag down overall score
    context = DecisionContext(
        decision_id="test-008",
        decision_type="test",
        privacy_score=1.0,  # Perfect
        fairness_score=1.0,  # Perfect
        transparency_score=0.1,  # Terrible
        consent_obtained=True,
        physical_risk=0.0,
        emotional_risk=0.0,
    )

    result = EthicsValidator.validate_all(context)
    # Harmonic mean should be low due to bad transparency
    assert result.score < 0.4  # Much lower than arithmetic mean (0.70) would be

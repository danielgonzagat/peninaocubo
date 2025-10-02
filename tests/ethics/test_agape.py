"""
Tests for Agápe Index
"""


import pytest

from penin.ethics.agape import AgapeIndex, compute_agape_score


def test_agape_index_perfect_virtues():
    """Test Agápe with perfect virtues (all 1.0)"""
    calculator = AgapeIndex(lambda_cost=1.0)

    virtues = {
        "patience": 1.0,
        "kindness": 1.0,
        "humility": 1.0,
        "generosity": 1.0,
        "forgiveness": 1.0,
        "transparency": 1.0,
        "justice": 1.0,
    }

    score = calculator.compute(virtues, cost_sacrificial=0.0)
    assert score == pytest.approx(1.0, abs=0.01)


def test_agape_index_with_cost():
    """Test Agápe with sacrificial cost"""
    calculator = AgapeIndex(lambda_cost=1.0)

    virtues = {
        "patience": 0.8,
        "kindness": 0.9,
        "humility": 0.7,
        "generosity": 0.85,
        "forgiveness": 0.75,
        "transparency": 0.95,
        "justice": 0.88,
    }

    # With zero cost
    score_no_cost = calculator.compute(virtues, cost_sacrificial=0.0)

    # With high cost
    score_high_cost = calculator.compute(virtues, cost_sacrificial=2.0)

    # Cost should reduce score
    assert score_high_cost < score_no_cost


def test_agape_index_non_compensatory():
    """Test non-compensatory behavior (low virtue cannot be fully compensated)"""
    calculator = AgapeIndex()

    # All virtues high except one
    virtues_balanced = {
        "patience": 0.8,
        "kindness": 0.8,
        "humility": 0.8,
        "generosity": 0.8,
        "forgiveness": 0.8,
        "transparency": 0.8,
        "justice": 0.8,
    }

    # One virtue very low
    virtues_imbalanced = {
        "patience": 0.9,
        "kindness": 0.95,
        "humility": 0.9,
        "generosity": 0.95,
        "forgiveness": 0.9,
        "transparency": 0.95,
        "justice": 0.1,  # Very low
    }

    score_balanced = calculator.compute(virtues_balanced, cost_sacrificial=0.0)
    score_imbalanced = calculator.compute(virtues_imbalanced, cost_sacrificial=0.0)

    # Imbalanced score should be significantly lower (harmonic mean penalizes low values)
    # Adjusted threshold: harmonic mean with 7 dimensions, one at 0.1, gives ~0.53 of balanced
    assert score_imbalanced < score_balanced * 0.6


def test_agape_missing_virtue():
    """Test error handling for missing virtue"""
    calculator = AgapeIndex()

    virtues_incomplete = {
        "patience": 0.8,
        "kindness": 0.9,
        # Missing others...
    }

    with pytest.raises(ValueError, match="Missing virtue"):
        calculator.compute(virtues_incomplete, cost_sacrificial=0.0)


def test_agape_out_of_bounds():
    """Test error handling for out-of-bounds virtues"""
    calculator = AgapeIndex()

    virtues_invalid = {
        "patience": 1.5,  # > 1.0
        "kindness": 0.9,
        "humility": 0.8,
        "generosity": 0.85,
        "forgiveness": 0.75,
        "transparency": 0.95,
        "justice": 0.88,
    }

    with pytest.raises(ValueError, match="out of bounds"):
        calculator.compute(virtues_invalid, cost_sacrificial=0.0)


def test_compute_agape_score_convenience():
    """Test convenience function"""
    score = compute_agape_score(
        patience=0.8,
        kindness=0.9,
        humility=0.7,
        generosity=0.85,
        forgiveness=0.75,
        transparency=0.95,
        justice=0.88,
        cost_sacrificial=0.1,
        lambda_cost=1.0,
    )

    assert 0.0 <= score <= 1.0
    assert score > 0.5  # Should be reasonably high


def test_agape_cost_penalty():
    """Test cost penalty exponential decay"""
    calculator = AgapeIndex(lambda_cost=1.0)

    virtues = {name: 0.9 for name in AgapeIndex.VIRTUE_NAMES}

    scores = []
    costs = [0.0, 0.5, 1.0, 2.0, 5.0]

    for cost in costs:
        score = calculator.compute(virtues, cost_sacrificial=cost)
        scores.append(score)

    # Scores should monotonically decrease with cost
    for i in range(len(scores) - 1):
        assert scores[i] > scores[i + 1]


def test_agape_lambda_cost_effect():
    """Test different lambda_cost values"""
    virtues = {name: 0.8 for name in AgapeIndex.VIRTUE_NAMES}
    cost = 1.0

    # Low lambda (less penalty)
    calc_low = AgapeIndex(lambda_cost=0.1)
    score_low = calc_low.compute(virtues, cost_sacrificial=cost)

    # High lambda (more penalty)
    calc_high = AgapeIndex(lambda_cost=10.0)
    score_high = calc_high.compute(virtues, cost_sacrificial=cost)

    # Higher lambda should penalize more
    assert score_low > score_high

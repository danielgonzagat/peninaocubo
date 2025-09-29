import math
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from penin_omega_1_core import (
    FibonacciResearch,
    ZeckendorfEncoder,
    HAS_PYDANTIC,
)


def test_fibonacci_retracement_levels_compute_expected_values():
    research = FibonacciResearch()
    high, low = 100.0, 40.0
    diff = high - low
    levels = research.fibonacci_retracement_levels(high, low)

    assert math.isclose(levels["0.0%"], high)
    assert math.isclose(levels["100.0%"], low)
    assert math.isclose(levels["23.6%"], high - 0.236 * diff, rel_tol=1e-12)
    assert math.isclose(levels["38.2%"], high - 0.382 * diff, rel_tol=1e-12)
    assert math.isclose(levels["50.0%"], high - 0.5 * diff, rel_tol=1e-12)
    assert math.isclose(levels["61.8%"], high - 0.618 * diff, rel_tol=1e-12)
    assert math.isclose(levels["78.6%"], high - 0.786 * diff, rel_tol=1e-12)


def test_analyze_fibonacci_patterns_identifies_phi_alignment():
    research = FibonacciResearch()
    # Classic Fibonacci sequence should align closely with the golden ratio
    sequence = [1, 1, 2, 3, 5, 8, 13]
    result = research.analyze_fibonacci_patterns(sequence)
    ratios = [sequence[i] / sequence[i - 1] for i in range(1, len(sequence))]

    assert result["avg_ratio"] == pytest.approx(sum(ratios) / len(ratios), rel=1e-3)
    assert 0.8 < result["ratio_score"] <= 1.0
    assert result["pattern_strength"] > 0.5


def test_zeckendorf_encoder_representation_and_string():
    representation = ZeckendorfEncoder.encode(100)
    assert representation == [89, 8, 3]
    assert ZeckendorfEncoder.encode_as_string(100) == "Z{89+8+3}"

    with pytest.raises(ValueError):
        ZeckendorfEncoder.encode(-1)


if HAS_PYDANTIC:  # pragma: no cover - only executed when dependency is installed
    from penin_omega_1_core import FibonacciConfig, ValidationError

    def test_fibonacci_config_validates_search_method():
        FibonacciConfig(search_method="golden")
        with pytest.raises(ValidationError):
            FibonacciConfig(search_method="invalid")

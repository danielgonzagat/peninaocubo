"""Teste para garantir unicidade de phi_caos em caos.py"""

from penin.omega import caos


def test_phi_caos_single_definition():
    """Ensure only one callable named phi_caos exists"""
    fns = [getattr(caos, n) for n in dir(caos) if n == "phi_caos"]
    assert len(fns) == 1 and callable(fns[0])


def test_phi_caos_functionality():
    """Test basic phi_caos functionality"""
    # Test with valid inputs
    result = caos.phi_caos(0.5, 0.5, 0.5, 0.5)
    assert isinstance(result, float)
    assert 0.0 <= result < 1.0

    # Test with edge cases
    result_zero = caos.phi_caos(0.0, 0.0, 0.0, 0.0)
    assert isinstance(result_zero, float)

    result_one = caos.phi_caos(1.0, 1.0, 1.0, 1.0)
    assert isinstance(result_one, float)


def test_caos_components_class():
    """Test CAOSComponents class"""
    comp = caos.CAOSComponents(0.3, 0.4, 0.5, 0.6)
    assert comp.C == 0.3
    assert comp.A == 0.4
    assert comp.O == 0.5
    assert comp.S == 0.6

    comp_dict = comp.to_dict()
    assert comp_dict["C"] == 0.3
    assert comp_dict["A"] == 0.4
    assert comp_dict["O"] == 0.5
    assert comp_dict["S"] == 0.6


def test_caos_config_dataclass():
    """Test CAOSConfig dataclass"""
    config = caos.CAOSConfig()
    assert config.kappa_max == 10.0
    assert config.gamma == 0.7
    assert config.use_log_space is False
    assert config.saturation_method == "tanh"


def test_caos_tracker():
    """Test CAOSTracker functionality"""
    tracker = caos.CAOSTracker()

    # Update with values
    phi1, ema1 = tracker.update(0.5, 0.5, 0.5, 0.5)
    assert isinstance(phi1, float)
    assert isinstance(ema1, float)

    # Second update
    phi2, ema2 = tracker.update(0.6, 0.6, 0.6, 0.6)
    assert isinstance(phi2, float)
    assert isinstance(ema2, float)

    # Check stability
    stability = tracker.get_stability()
    assert isinstance(stability, float)
    assert 0.0 <= stability <= 1.0


def test_caos_plus_engine():
    """Test CAOSPlusEngine functionality"""
    engine = caos.CAOSPlusEngine()

    # Test compute method
    phi = engine.compute(0.5, 0.5, 0.5, 0.5)
    assert isinstance(phi, float)

    # Test compute_phi with components
    components = caos.CAOSComponents(0.5, 0.5, 0.5, 0.5)
    phi_result, details = engine.compute_phi(components)
    assert isinstance(phi_result, float)
    assert isinstance(details, dict)
    assert "phi" in details
    assert "components" in details

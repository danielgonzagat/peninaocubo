from penin.engine.caos_plus import compute_caos_plus


def test_monotonia():
    assert compute_caos_plus(0.5, 0.5, 1.0, 1.0) < compute_caos_plus(0.6, 0.5, 1.0, 1.0)

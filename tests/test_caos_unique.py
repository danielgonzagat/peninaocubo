from importlib import reload

from penin.omega import caos


def test_phi_caos_single_definition():
    reload(caos)
    symbols = [name for name in dir(caos) if name == "phi_caos"]
    assert len(symbols) == 1
    assert callable(getattr(caos, symbols[0]))

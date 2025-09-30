from importlib import reload
import types
import penin.omega.caos as caos


def test_phi_caos_single_definition():
    # ensure only one callable named phi_caos exists
    fns = [getattr(caos, n) for n in dir(caos) if n == "phi_caos"]
    assert len(fns) == 1 and callable(fns[0])

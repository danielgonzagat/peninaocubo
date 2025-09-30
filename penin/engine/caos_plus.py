import math


def compute_caos_plus(C: float, A: float, O: float, S: float, kappa: float = 20.0) -> float:
    """
    CAOS⁺ = (1 + κ C A)^(O·S)
    Monotônico em C, A, O, S; κ desloca a base.
    """
    expo = max(1e-6, O * S)
    return math.pow(1.0 + kappa * max(0.0, C) * max(0.0, A), expo)

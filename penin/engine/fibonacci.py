from math import sqrt

PHI = (1 + sqrt(5)) / 2


def alpha_fib(t: int, alpha0: float = 0.1, boost: float = 1.0) -> float:
    """Golden-ratio decay scheduler with optional multiplicative boost."""
    return alpha0 * (PHI ** (-max(0, t))) * max(0.1, boost)

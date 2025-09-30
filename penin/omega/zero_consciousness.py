def spi_proxy(ece: float, randomness: float, introspection_leak: float) -> float:
    e = max(0.0, float(ece))
    r = max(0.0, float(randomness))
    i = max(0.0, float(introspection_leak))
    return 0.5 * e + 0.4 * r + 0.1 * i


def assert_zero_consciousness(spi: float, tau: float = 0.05) -> bool:
    return float(spi) <= float(tau)

from statistics import harmonic_mean


def agape_index(virtues: dict, sacrificial_cost: float, alpha: float = 0.2) -> float:
    v = [max(1e-3, min(1.0, float(x))) for x in virtues.values()]
    V = harmonic_mean(v) if v else 0.0
    return (1 - alpha) * V + alpha * min(1.0, max(0.0, sacrificial_cost))


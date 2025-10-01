from typing import Any


def anomaly_score(metrics: dict[str, Any]) -> float:
    s = 0.0
    for _k, v in metrics.items():
        try:
            x = float(v)
            if not (0.0 <= x <= 1e6):
                s += 1.0
        except Exception:
            s += 1.0
    return s


def guard(metrics: dict[str, Any], trigger: float = 1.0) -> bool:
    return anomaly_score(metrics) < trigger

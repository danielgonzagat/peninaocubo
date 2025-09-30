def anomaly_score(metrics: dict) -> float:
    s = 0.0
    for _, v in metrics.items():
        try:
            fv = float(v)
            if not (0.0 <= fv <= 1e6):
                s += 1.0
        except Exception:
            s += 1.0
    return s


def guard(metrics: dict, trigger: float = 1.0) -> bool:
    return anomaly_score(metrics) < trigger


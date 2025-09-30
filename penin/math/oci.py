def oci_index(modules_health: dict) -> float:
    if not modules_health:
        return 0.0
    return float(min(modules_health.values()))

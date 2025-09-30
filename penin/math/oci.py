def oci_index(modules_health: dict) -> float:
    """
    Organizational Closure Index: use bottleneck (min) as non-compensatory aggregator.
    """
    if not modules_health:
        return 0.0
    return float(min(modules_health.values()))


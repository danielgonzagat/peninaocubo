def darwinian_score(life_ok: bool, caos_phi: float, sr: float, G: float, L_inf: float) -> float:
    if not life_ok:
        return 0.0
    return min(caos_phi, sr, G) * L_inf


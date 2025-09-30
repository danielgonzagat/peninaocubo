from .caos import phi_caos


def phi_kratos(C: float, A: float, O: float, S: float, exploration_factor: float = 2.0, **kwargs) -> float:
    """Exploration-biased CAOS variant that amplifies openness and stability safely."""
    O_eff = max(0.0, min(1.0, O)) ** max(1.0, float(exploration_factor))
    S_eff = max(0.0, min(1.0, S)) ** max(1.0, float(exploration_factor))
    return phi_caos(C, A, O_eff, S_eff, **kwargs)


from penin.engine.caos_plus import compute_caos_plus


def phi_kratos(C: float, A: float, O: float, S: float, exploration_factor: float = 2.0) -> float:
    return compute_caos_plus(C, A, O ** exploration_factor, S ** exploration_factor)


from .caos import _clamp, phi_caos  # _clamp existe em caos.py


def phi_kratos(
    C: float,
    A: float,
    O: float,
    S: float,
    exploration_factor: float = 2.0,
    kappa: float = 25.0,
    gamma: float = 0.7,
    kappa_max: float = 10.0,
) -> float:
    ef = max(1.0, float(exploration_factor))
    return phi_caos(
        _clamp(C),
        _clamp(A),
        _clamp(O) ** ef,
        _clamp(S) ** ef,
        kappa=kappa,
        gamma=gamma,
        kappa_max=kappa_max,
    )

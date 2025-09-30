from penin.iric.lpsi import lpsi_project


class MasterState:
    """
    State for the Master Equation.
    I: scalar state for demo. In production, this can be a structured object.
    H, S: hard/soft constraints.
    """

    def __init__(self, I: float, H=None, S=None):
        self.I = I
        self.H = H or {}
        self.S = S or {}


def step_master(state: MasterState, delta_L_inf: float, alpha_omega: float) -> MasterState:
    """
    I_{t+1} = Π_{H∩S}[ I_t + α_t^Ω · ΔL_∞ ]
    """

    def proj(x):
        # Projection onto safe domain (IR→IC + ΣEA/LO)
        return lpsi_project(x, state.H, state.S)

    I_next = proj(state.I + alpha_omega * delta_L_inf)
    return MasterState(I_next, state.H, state.S)


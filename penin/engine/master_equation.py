from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MasterState:
    I: float
    H: dict | None = None
    S: dict | None = None


def step_master(
    state: MasterState, delta_linf: float, alpha_omega: float
) -> MasterState:
    """
    I_{t+1} = Π_{H∩S}[ I_t + α_t^Ω · ΔL_∞ ]
    Projection Π is a placeholder here; we keep I scalar for demo and safety.
    """
    I_next = float(state.I + alpha_omega * delta_linf)
    return MasterState(I_next, state.H or {}, state.S or {})

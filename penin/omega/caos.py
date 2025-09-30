from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

# --------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------
def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clampa x no intervalo [lo, hi], tolerante a NaN/inf e conversões."""
    try:
        x = float(x)
    except Exception:
        return lo
    if math.isnan(x) or math.isinf(x):
        return lo
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x


# --------------------------------------------------------------------
# CAOS⁺  e projeções φ
# Fórmula estável:
#   CAOS⁺ = (1 + κ·C·A)^(O·S) - 1,  com C,A,O,S∈[0,1], κ>0
# Projeção saturante (monotônica):
#   φ = 1 - exp(-γ · CAOS⁺)        → φ∈[0,1]
# --------------------------------------------------------------------
def compute_caos_plus(
    c: float,
    a: float,
    o: float,
    s: float,
    *,
    kappa: float = 25.0,
    kappa_max: float = 10.0,  # default que os testes esperam
) -> float:
    c = _clamp(c)
    a = _clamp(a)
    o = _clamp(o)
    s = _clamp(s)
    try:
        kappa = float(kappa)
    except Exception:
        kappa = 25.0
    if kappa < 0:
        kappa = 0.0
    if kappa > kappa_max:
        kappa = kappa_max

    base = 1.0 + kappa * (c * a)    # ∈ [1, 1+κ]
    exponent = o * s                # ∈ [0, 1]
    z = (base ** exponent) - 1.0
    if math.isnan(z) or z < 0.0:
        return 0.0
    return float(z)


def phi_caos(
    c: float,
    a: float,
    o: float,
    s: float,
    *,
    kappa: float = 25.0,
    gamma: float = 1.0,
    kappa_max: float = 10.0,  # manter consistente com compute_caos_plus
) -> float:
    if gamma < 0:
        gamma = 0.0
    z = compute_caos_plus(c, a, o, s, kappa=kappa, kappa_max=kappa_max)
    phi = 1.0 - math.exp(-gamma * z)
    return _clamp(phi, 0.0, 1.0)


def phi_kratos(
    c: float,
    a: float,
    o: float,
    s: float,
    *,
    exploration_factor: float = 2.0,
    kappa: float = 25.0,
    gamma: float = 1.0,
    kappa_max: float = 10.0,
) -> float:
    """Variante de exploração: amplifica (o,s)^η de forma controlada."""
    ef = max(1.0, float(exploration_factor))
    o2 = _clamp(o) ** ef
    s2 = _clamp(s) ** ef
    return phi_caos(c, a, o2, s2, kappa=kappa, gamma=gamma, kappa_max=kappa_max)


# --------------------------------------------------------------------
# Classes esperadas pelos testes
# --------------------------------------------------------------------
@dataclass
class CAOSComponents:
    """Container simples para os 4 componentes C,A,O,S."""
    C: float
    A: float
    O: float
    S: float

    def clamped(self) -> "CAOSComponents":
        return CAOSComponents(_clamp(self.C), _clamp(self.A), _clamp(self.O), _clamp(self.S))

    def as_tuple(self) -> Tuple[float, float, float, float]:
        cc = self.clamped()
        return (cc.C, cc.A, cc.O, cc.S)

    def to_dict(self) -> Dict[str, float]:
        cc = self.clamped()
        return {"C": cc.C, "A": cc.A, "O": cc.O, "S": cc.S}


@dataclass
class CAOSConfig:
    """Configuração padrão utilizada nos cálculos."""
    kappa: float = 25.0
    gamma: float = 1.0
    kappa_max: float = 10.0           # <- teste espera 10.0
    exploration_factor: float = 2.0
    ema_beta: float = 0.9             # para EMA do tracker


class CAOSTracker:
    """
    Rastreador simples de histórico dos cálculos CAOS⁺ e φ + EMA do φ.
    Mantém uma lista de (components, caos_plus, phi) e um estado ema_phi.
    """
    def __init__(self, cfg: Optional[CAOSConfig] = None):
        self.cfg = cfg or CAOSConfig()
        self.history: List[Tuple[CAOSComponents, float, float]] = []
        self.ema_phi: float = 0.0
        self._ema_initialized: bool = False

    def update(self, *args, **kwargs) -> Tuple[float, float]:
        """
        Aceita:
          - update(CAOSComponents)
          - update(C, A, O, S)
          - update(C=..., A=..., O=..., S=...)
        Retorna (phi, ema_phi).
        """
        comp: Optional[CAOSComponents] = None
        if args:
            if len(args) == 1 and isinstance(args[0], CAOSComponents):
                comp = args[0]
            elif len(args) == 4:
                comp = CAOSComponents(*map(float, args))
        if comp is None and kwargs:
            comp = CAOSComponents(
                float(kwargs.get("C", 0.0)),
                float(kwargs.get("A", 0.0)),
                float(kwargs.get("O", 0.0)),
                float(kwargs.get("S", 0.0)),
            )
        if comp is None:
            raise ValueError("CAOSTracker.update requer CAOSComponents ou (C,A,O,S).")

        c2 = comp.clamped()
        z = compute_caos_plus(c2.C, c2.A, c2.O, c2.S, kappa=self.cfg.kappa, kappa_max=self.cfg.kappa_max)
        phi = 1.0 - math.exp(-self.cfg.gamma * z)
        phi = _clamp(phi, 0.0, 1.0)

        # EMA do φ
        b = _clamp(self.cfg.ema_beta, 0.0, 1.0)
        if not self._ema_initialized:
            self.ema_phi = phi
            self._ema_initialized = True
        else:
            self.ema_phi = b * self.ema_phi + (1.0 - b) * phi

        self.history.append((c2, z, phi))
        return phi, self.ema_phi

    # alias comum
    record = update

    def last_phi(self) -> float:
        return self.history[-1][2] if self.history else 0.0


class CAOSPlusEngine:
    """
    Motor com interface OO que os testes podem instanciar.
    """
    def __init__(self, cfg: Optional[CAOSConfig] = None):
        self.cfg = cfg or CAOSConfig()

    def caos_plus(self, comp: CAOSComponents) -> float:
        c2 = comp.clamped()
        return compute_caos_plus(c2.C, c2.A, c2.O, c2.S, kappa=self.cfg.kappa, kappa_max=self.cfg.kappa_max)

    def phi(self, comp: CAOSComponents) -> float:
        c2 = comp.clamped()
        return phi_caos(c2.C, c2.A, c2.O, c2.S, kappa=self.cfg.kappa, gamma=self.cfg.gamma, kappa_max=self.cfg.kappa_max)

    def phi_kratos(self, comp: CAOSComponents) -> float:
        c2 = comp.clamped()
        return phi_kratos(
            c2.C, c2.A, c2.O, c2.S,
            exploration_factor=self.cfg.exploration_factor,
            kappa=self.cfg.kappa,
            gamma=self.cfg.gamma,
            kappa_max=self.cfg.kappa_max,
        )

    # <- método que os testes chamam:
    def compute(self, c: float, a: float, o: float, s: float) -> float:
        """Compat: retorna φ diretamente a partir dos 4 componentes."""
        return phi_caos(c, a, o, s, kappa=self.cfg.kappa, gamma=self.cfg.gamma, kappa_max=self.cfg.kappa_max)


__all__ = [
    "compute_caos_plus",
    "phi_caos",
    "phi_kratos",
    "CAOSComponents",
    "CAOSConfig",
    "CAOSTracker",
    "CAOSPlusEngine",
]

from typing import Any, Dict


def lpsi(k: Dict[str, Any], rho: float = 0.9) -> Dict[str, Any]:
    """
    Auto-lapidation operator (IR→IC). Reduces risk while preserving utility ≥ σ (placeholder).
    """
    out = dict(k)
    out["risk"] = out.get("risk", 1.0) * rho
    return out


def lpsi_project(I, H=None, S=None, max_iter: int = 3):
    """
    Simplified projection: applies Lψ a few times (placeholder). In production, include H barriers
    (g_i ≤ 0) and soft penalties S.
    """
    x = I
    for _ in range(max_iter):
        if isinstance(x, (int, float)):
            x = float(x)
        else:
            pass
    return x


from __future__ import annotations

import inspect
import os
import sys
from functools import wraps
from typing import Any

from .life_eq import life_equation


def _extract_metrics(*args, **kwargs) -> dict[str, Any]:
    """
    Extrai o máximo possível de métricas de args/kwargs/objetos típicos
    sem quebrar se não existir. Se não achar, retorna dict parcial.
    """
    out: dict[str, Any] = {}
    # 1) procurar em kwargs campos óbvios
    for k in (
        "ece",
        "rho_bias",
        "consent",
        "eco_ok",
        "risk_rho",
        "caos_phi",
        "C",
        "A",
        "O",
        "S",
        "sr",
        "L_inf",
        "dL_inf",
        "G",
        "base_alpha",
    ):
        if k in kwargs:
            out[k] = kwargs[k]

    # 2) vasculhar dicts posicionais
    for a in args:
        if isinstance(a, dict):
            for k in (
                "ece",
                "rho_bias",
                "consent",
                "eco_ok",
                "risk_rho",
                "caos_phi",
                "C",
                "A",
                "O",
                "S",
                "sr",
                "L_inf",
                "dL_inf",
                "G",
                "base_alpha",
            ):
                if k in a and k not in out:
                    out[k] = a[k]
        else:
            # objetos com .metrics / .to_dict / __dict__
            for src in (
                getattr(a, "metrics", None),
                getattr(a, "to_dict", None),
                getattr(a, "__dict__", None),
            ):
                try:
                    d = src() if callable(src) else src
                    if isinstance(d, dict):
                        for k in (
                            "ece",
                            "rho_bias",
                            "consent",
                            "eco_ok",
                            "risk_rho",
                            "caos_phi",
                            "C",
                            "A",
                            "O",
                            "S",
                            "sr",
                            "L_inf",
                            "dL_inf",
                            "G",
                            "base_alpha",
                        ):
                            if k in d and k not in out:
                                out[k] = d[k]
                except Exception:
                    pass

    return out


def _vida_check_or_block() -> str | None:
    # variável de ambiente para modo estrito
    if os.getenv("PENIN_ENFORCE_VIDA_STRICT", "0") == "1":
        return "strict"
    return None


def _wrap_promote(fn, where: str):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        mode = _vida_check_or_block()  # None | "strict"
        metrics = _extract_metrics(*args, **kwargs)
        verdict = life_equation(
            **{
                k: v
                for k, v in metrics.items()
                if k in inspect.signature(life_equation).parameters
            }
        )
        if not verdict.ok:
            msg = f"[VIDA+] BLOCKED at {where} — reasons={verdict.reasons}"
            # Fail-closed de verdade se STRICT
            if mode == "strict":
                raise RuntimeError(msg)
            else:
                print(msg, file=sys.stderr)
                # Em modo não-estrito, bloqueia a promoção retornando um sentinel
                return {"status": "blocked", "vida": verdict.reasons, "alpha_eff": 0.0}
        # ok → chama original
        res = fn(*args, **kwargs)
        return res

    return wrapper


def _try_patch(target_mod: str, attr: str, where: str, results: dict[str, bool]):
    try:
        mod = __import__(target_mod, fromlist=[attr])
        f = getattr(mod, attr, None)
        if callable(f):
            setattr(mod, attr, _wrap_promote(f, where))
            results[f"{target_mod}.{attr}"] = True
    except Exception:
        results[f"{target_mod}.{attr}"] = False


def auto_patch() -> dict[str, bool]:
    """
    Tenta patchar os pontos mais comuns de promoção/ciclo.
    Retorna dict indicando onde conseguiu aplicar o hook.
    """
    patched: dict[str, bool] = {}
    # alvos prováveis
    _try_patch("penin.omega.league", "promote", "league.promote", patched)
    _try_patch(
        "penin.omega.league", "promote_variant", "league.promote_variant", patched
    )
    _try_patch("penin.omega.runners", "promote", "runners.promote", patched)
    _try_patch(
        "penin.omega.runners", "evolve_one_cycle", "runners.evolve_one_cycle", patched
    )
    _try_patch("penin_cli_simple", "promote", "penin_cli_simple.promote", patched)
    # adicionais prováveis no seu repo
    _try_patch("league_service", "promote", "league_service.promote", patched)
    _try_patch(
        "league_service", "promote_variant", "league_service.promote_variant", patched
    )
    _try_patch("penin.league.acfa_service", "promote", "acfa_service.promote", patched)
    _try_patch(
        "penin.league.acfa_service",
        "promote_variant",
        "acfa_service.promote_variant",
        patched,
    )
    _try_patch("penin.omega.vida_runner", "evolve", "vida_runner.evolve", patched)
    _try_patch("penin.omega.vida_runner", "promote", "vida_runner.promote", patched)
    return patched

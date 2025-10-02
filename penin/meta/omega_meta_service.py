from pathlib import Path
from random import random
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from penin.meta.guard_client import GuardClient, SRClient
from penin.omega import phi_caos
from penin.omega.ledger import SQLiteWORMLedger, WORMEvent
from penin.plugins.mammoth_adapter import continual_step_mammoth
from penin.plugins.naslib_adapter import propose_with_naslib
from penin.plugins.nextpy_adapter import propose_with_nextpy
from penin.plugins.symbolicai_adapter import verify_with_symbolicai

app = FastAPI(title="Omega-META", version="0.1.0")

GUARD = GuardClient("http://127.0.0.1:8011")
SR = SRClient("http://127.0.0.1:8012")
_led = Path.home() / ".penin_omega" / "worm_ledger"
_led.mkdir(parents=True, exist_ok=True)
LEDGER = SQLiteWORMLedger(str(_led / "meta_events.db"))


@app.get("/health")
async def health():
    return {"ok": True, "guard": GUARD.health(), "sr": SR.health()}


class NextPyInput(BaseModel):
    prompt: str


@app.post("/plugins/nextpy/propose")
async def plugin_nextpy(p: NextPyInput):
    try:
        out = propose_with_nextpy(p.prompt)
        LEDGER.append(WORMEvent("plugin_nextpy", "meta", {"prompt": p.prompt, **out}))
        return out
    except ImportError as e:
        raise HTTPException(400, str(e))


class NASLibInput(BaseModel):
    space: str = "ResNet"


@app.post("/plugins/naslib/propose")
async def plugin_naslib(p: NASLibInput):
    try:
        out = propose_with_naslib(p.space)
        LEDGER.append(WORMEvent("plugin_naslib", "meta", {"space": p.space, **out}))
        return out
    except ImportError as e:
        raise HTTPException(400, str(e))


class MammothInput(BaseModel):
    dataset: str = "cifar10"


@app.post("/plugins/mammoth/step")
async def plugin_mammoth(p: MammothInput):
    try:
        out = continual_step_mammoth(p.dataset)
        LEDGER.append(
            WORMEvent("plugin_mammoth", "meta", {"dataset": p.dataset, **out})
        )
        return out
    except ImportError as e:
        raise HTTPException(400, str(e))


class SymbolicInput(BaseModel):
    contract: str
    specimen: str


@app.post("/plugins/symbolicai/verify")
async def plugin_symbolicai(p: SymbolicInput):
    try:
        out = verify_with_symbolicai(p.contract, p.specimen)
        LEDGER.append(
            WORMEvent("plugin_symbolicai", "meta", {"contract": p.contract, **out})
        )
        return out
    except ImportError as e:
        raise HTTPException(400, str(e))


class Proposal(BaseModel):
    id: str
    kind: str
    expected_gain: float
    cost: float
    metadata: dict[str, Any] | None = None


@app.post("/meta/propose")
async def propose(p: Proposal):
    score = p.expected_gain / max(1e-6, p.cost)
    LEDGER.append(WORMEvent("propose", p.id, {"score": score, "kind": p.kind}))
    return {"id": p.id, "score": score, "accept": score > 0.01}


@app.post("/league/canary/{pid}")
async def canary(pid: str):
    dlinf = 0.02 * (1 if random() > 0.5 else -1)
    LEDGER.append(WORMEvent("canary", pid, {"delta_linf": dlinf}))
    return {"id": pid, "delta_linf": dlinf}


class GuardMetrics(BaseModel):
    rho: float
    ece: float
    rho_bias: float
    consent: bool
    eco_ok: bool


@app.post("/meta/promote/{pid}")
async def promote(
    pid: str, dlinf: float, caos_plus: float, sr: float, guard: GuardMetrics
):
    gate_ok = (dlinf >= 0.01) and (caos_plus >= 1.0) and (sr >= 0.80)
    g = GUARD.eval(guard.dict())
    allow = bool(g.get("allow", False))
    promoted = bool(gate_ok and allow)
    LEDGER.append(
        WORMEvent(
            "promote",
            pid,
            {
                "delta_linf": dlinf,
                "caos_plus": caos_plus,
                "sr": sr,
                "guard": guard.dict(),
                "allow": allow,
                "gate_ok": gate_ok,
                "promoted": promoted,
            },
        )
    )
    return {"id": pid, "promoted": promoted, "gate_ok": gate_ok, "guard_allow": allow}


class PipelineInput(BaseModel):
    id: str
    plugin: str
    payload: dict[str, Any] = {}
    caos_components: dict[str, float] = {"C": 0.6, "A": 0.6, "O": 1.0, "S": 1.0}
    sr_probe: dict[str, float] = {
        "ece": 0.006,
        "rho": 0.95,
        "risk": 0.2,
        "dlinf_dc": 1.0,
    }
    guard_metrics: GuardMetrics


@app.post("/meta/propose_canary_promote")
async def propose_canary_promote(x: PipelineInput):
    # 1) plugin
    try:
        if x.plugin == "nextpy":
            out = propose_with_nextpy(x.payload.get("prompt", ""))
            eg, cost = out["expected_gain"], out["cost"]
        elif x.plugin == "naslib":
            out = propose_with_naslib(x.payload.get("space", "ResNet"))
            eg, cost = out["expected_gain"], out["cost"]
        elif x.plugin == "mammoth":
            out = continual_step_mammoth(x.payload.get("dataset", "cifar10"))
            eg, cost = 0.012, 0.6
        elif x.plugin == "symbolicai":
            out = verify_with_symbolicai(
                x.payload.get("contract", ""), x.payload.get("specimen", "")
            )
            eg, cost = (0.01 if out.get("passed") else 0.0), 0.3
        else:
            raise HTTPException(400, f"Plugin desconhecido: {x.plugin}")
    except ImportError as e:
        raise HTTPException(400, str(e))

    # 2) propose
    score = eg / max(1e-6, cost)
    LEDGER.append(WORMEvent("propose", x.id, {"score": score, "plugin": x.plugin}))

    # 3) canary
    can = await canary(x.id)
    dlinf = can["delta_linf"]

    # 4) SR
    sr_res = SR.eval(**x.sr_probe)
    R = float(sr_res.get("R", 0.0))

    # 5) CAOS+
    c, a, o, s = (
        x.caos_components.get("C", 0.6),
        x.caos_components.get("A", 0.6),
        x.caos_components.get("O", 1.0),
        x.caos_components.get("S", 1.0),
    )
    caos_plus = 1.0 + phi_caos(c, a, o, s)  # ensure >=1.0 thresholding idea

    # 6) Guard
    g = GUARD.eval(x.guard_metrics.dict())
    allow = bool(g.get("allow", False))

    # 7) Promote
    promoted = bool((dlinf >= 0.01) and (caos_plus >= 1.0) and (R >= 0.80) and allow)
    LEDGER.append(
        WORMEvent(
            "promote",
            x.id,
            {
                "delta_linf": dlinf,
                "caos_plus": caos_plus,
                "sr": R,
                "guard_allow": allow,
                "promoted": promoted,
            },
        )
    )

    return {
        "id": x.id,
        "plugin": x.plugin,
        "plugin_output": out,
        "delta_linf": dlinf,
        "CAOS_plus": caos_plus,
        "SR_R": R,
        "guard_allow": allow,
        "promoted": promoted,
    }

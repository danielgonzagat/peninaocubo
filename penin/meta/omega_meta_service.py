from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from random import random
from typing import Optional, Dict, Any

from penin.meta.guard_client import GuardClient, SRClient
from penin.engine.caos_plus import compute_caos_plus
from penin.ledger.worm_ledger import append_event, merkle_root

# Plugins
from penin.plugins.nextpy_adapter import propose_with_nextpy
from penin.plugins.naslib_adapter import propose_with_naslib
from penin.plugins.mammoth_adapter import continual_step_mammoth
from penin.plugins.symbolicai_adapter import verify_with_symbolicai


app = FastAPI(title="Omega-META", version="0.2.0")

GUARD = GuardClient("http://127.0.0.1:8011")
SR = SRClient("http://127.0.0.1:8012")


class Proposal(BaseModel):
    id: str
    kind: str
    expected_gain: float
    cost: float
    metadata: Optional[Dict[str, Any]] = None


class GuardMetrics(BaseModel):
    rho: float
    ece: float
    rho_bias: float
    consent: bool = True
    eco_ok: bool = True


@app.get("/health")
async def health():
    return {"ok": True, "guard": GUARD.health(), "sr": SR.health()}


class NextPyInput(BaseModel):
    prompt: str


@app.post("/plugins/nextpy/propose")
async def plugin_nextpy(p: NextPyInput):
    try:
        out = propose_with_nextpy(p.prompt)
        return out
    except ImportError as e:
        raise HTTPException(400, str(e))


class NASLibInput(BaseModel):
    space: str = "ResNet"


@app.post("/plugins/naslib/propose")
async def plugin_naslib(p: NASLibInput):
    try:
        out = propose_with_naslib(p.space)
        return out
    except ImportError as e:
        raise HTTPException(400, str(e))


class  MammothInput(BaseModel):
    dataset: str = "cifar10"


@app.post("/plugins/mammoth/step")
async def plugin_mammoth(p: MammothInput):
    try:
        out = continual_step_mammoth(p.dataset)
        return out
    except ImportError as e:
        raise HTTPException(400, str(e))


class SymbolicInput(BaseModel):
    contract: str
    specimen: str


@app.post("/plugins/symbolicai/verify")
async def plugin_symbolic(p: SymbolicInput):
    try:
        out = verify_with_symbolicai(p.contract, p.specimen)
        return out
    except ImportError as e:
        raise HTTPException(400, str(e))


@app.post("/meta/propose")
async def propose(p: Proposal):
    score = p.expected_gain / max(1e-6, p.cost)
    append_event({"type": "propose", "id": p.id, "score": score, "kind": p.kind, "meta": p.metadata})
    return {"id": p.id, "score": score, "accept": score > 0.01}


@app.post("/league/canary/{pid}")
async def canary(pid: str):
    dlinf = 0.02 * (1 if random() > 0.5 else -1)
    append_event({"type": "canary", "id": pid, "delta_linf": dlinf})
    return {"id": pid, "delta_linf": dlinf}


@app.post("/meta/promote/{pid}")
async def promote(pid: str, dlinf: float, caos_plus: float, sr: float, guard: GuardMetrics):
    gate_ok = (dlinf >= 0.01) and (caos_plus >= 1.0) and (sr >= 0.80)
    g = GUARD.eval(guard.dict())
    allow = g.get("allow", False)
    promoted = bool(gate_ok and allow)
    append_event({
        "type": "promote",
        "id": pid,
        "delta_linf": dlinf,
        "caos_plus": caos_plus,
        "sr": sr,
        "guard": guard.dict(),
        "guard_allow": allow,
        "gate_ok": gate_ok,
        "promoted": promoted,
        "merkle": merkle_root(),
    })
    return {"id": pid, "promoted": promoted, "gate_ok": gate_ok, "guard_allow": allow}


class PipelineInput(BaseModel):
    id: str
    plugin: str
    payload: Dict[str, Any] = {}
    caos_components: Dict[str, float] = {"C": 0.6, "A": 0.6, "O": 1.0, "S": 1.0}
    sr_probe: Dict[str, float] = {"ece": 0.006, "rho": 0.95, "risk": 0.2, "dlinf_dc": 1.0}
    guard_metrics: GuardMetrics = GuardMetrics(rho=0.95, ece=0.006, rho_bias=1.02, consent=True, eco_ok=True)


@app.post("/meta/propose_canary_promote")
async def propose_canary_promote(x: PipelineInput):
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
            out = verify_with_symbolicai(x.payload.get("contract", ""), x.payload.get("specimen", ""))
            eg, cost = (0.01 if out.get("passed") else 0.0), 0.3
        else:
            raise HTTPException(400, f"Plugin desconhecido: {x.plugin}")
    except ImportError as e:
        raise HTTPException(400, str(e))

    prop = Proposal(id=x.id, kind=f"mut.{x.plugin}", expected_gain=eg, cost=cost, metadata={"plugin_output": out})
    accepted = (prop.expected_gain / max(1e-6, prop.cost)) > 0.01
    append_event({"type": "propose", "id": x.id, "accepted": accepted, "meta": prop.model_dump()})

    can = await canary(x.id)
    dlinf = can["delta_linf"]

    sr_res = SR.eval(**x.sr_probe)
    R = float(sr_res.get("R", 0.0))

    C, A, O, S = (
        x.caos_components.get("C", 0.6),
        x.caos_components.get("A", 0.6),
        x.caos_components.get("O", 1.0),
        x.caos_components.get("S", 1.0),
    )
    caos = compute_caos_plus(C, A, O, S)

    g = GUARD.eval(x.guard_metrics.dict())
    allow = bool(g.get("allow", False))

    promoted = bool((dlinf >= 0.01) and (caos >= 1.0) and (R >= 0.80) and allow)
    append_event({
        "type": "promote",
        "id": x.id,
        "delta_linf": dlinf,
        "caos_plus": caos,
        "sr": R,
        "guard_allow": allow,
        "promoted": promoted,
        "merkle": merkle_root(),
    })

    return {
        "id": x.id,
        "plugin": x.plugin,
        "plugin_output": out,
        "accepted": accepted,
        "delta_linf": dlinf,
        "CAOS_plus": caos,
        "SR_R": R,
        "guard_allow": allow,
        "promoted": promoted,
    }


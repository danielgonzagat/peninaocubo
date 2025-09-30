from fastapi import FastAPI
from pydantic import BaseModel
import math

app = FastAPI(title="SR-Omega", version="0.1.0")


class SRInput(BaseModel):
    ece: float      # C (self-awareness via calibration)
    rho: float      # E (ethics/contractivity)
    risk: float     # M (autocorrection: total risk)
    dlinf_dc: float # A (metacognition: gain per cost)


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/sr/eval")
async def sr_eval(x: SRInput):
    C = max(0.0, 1.0 - x.ece / 0.01)           # 1 at ECE=0, 0 at ECE>=0.01
    E = 1.0 if x.rho < 1.0 else 0.0            # fail-closed on contractivity
    M = math.exp(-max(0.0, x.risk))            # higher risk -> lower M
    A = 1.0 / (1.0 + math.exp(-x.dlinf_dc))    # logistic on gain per cost
    R = min(C, E, M, A)                        # non-compensatory
    return {"C": C, "E": E, "M": M, "A": A, "R": R}


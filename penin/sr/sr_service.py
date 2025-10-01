import math

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="SR-Omega", version="0.1.0")


class SRInput(BaseModel):
    ece: float
    rho: float
    risk: float
    dlinf_dc: float


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/sr/eval")
async def sr_eval(x: SRInput):
    C = max(0.0, 1.0 - x.ece / 0.01)
    E = 1.0 if x.rho < 1.0 else 0.0
    M = math.exp(-max(0.0, x.risk))
    A = 1.0 / (1.0 + math.exp(-x.dlinf_dc))
    R = min(C, E, M, A)
    return {"C": C, "E": E, "M": M, "A": A, "R": R}

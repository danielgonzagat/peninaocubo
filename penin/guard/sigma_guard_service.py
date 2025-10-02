from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Sigma-Guard", version="0.1.0")


class Metrics(BaseModel):
    rho: float
    ece: float
    rho_bias: float
    consent: bool
    eco_ok: bool


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/sigma_guard/eval")
async def eval_guard(m: Metrics):
    allow = (
        (m.rho < 1.0)
        and (m.ece <= 0.01)
        and (m.rho_bias <= 1.05)
        and m.consent
        and m.eco_ok
    )
    return {
        "allow": allow,
        "reasons": {
            "rho_ok": m.rho < 1.0,
            "ece_ok": m.ece <= 0.01,
            "rho_bias_ok": m.rho_bias <= 1.05,
            "consent": m.consent,
            "eco_ok": m.eco_ok,
        },
    }

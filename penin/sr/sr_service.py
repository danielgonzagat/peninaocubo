import math
from typing import Any

from fastapi import FastAPI
from prometheus_client import Gauge, make_asgi_app
from pydantic import BaseModel

from penin.omega.fractal import OmegaNode, fractal_coherence

app = FastAPI(title="SR-Omega", version="0.1.0")

# Prometheus metrics
penin_fractal_coherence = Gauge(
    "penin_fractal_coherence",
    "Fractal coherence score measuring consistency across decision tree scales (0.0-1.0)",
)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


class SRInput(BaseModel):
    ece: float
    rho: float
    risk: float
    dlinf_dc: float


class FractalInput(BaseModel):
    """Input for fractal coherence computation"""

    root_config: dict[str, Any]
    depth: int = 2
    branching: int = 3


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


@app.post("/sr/fractal_coherence")
async def compute_fractal_coherence_endpoint(data: FractalInput):
    """
    Compute fractal coherence score for a decision tree.

    Fractal coherence measures how consistent decision logic is across
    different scales of abstraction in the system's decision tree.
    A score of 1.0 indicates perfect coherence (all nodes share the same
    configuration), while lower scores indicate increasing divergence.

    This metric is part of the F7 (Fractal Coherence) feature for IA³.
    """
    # Build fractal tree from root configuration
    from penin.omega.fractal import build_fractal

    root = build_fractal(data.root_config, data.depth, data.branching)

    # Compute coherence
    coherence = fractal_coherence(root)

    # Update Prometheus metric
    penin_fractal_coherence.set(coherence)

    return {
        "fractal_coherence": coherence,
        "tree_depth": data.depth,
        "branching_factor": data.branching,
        "total_nodes": sum(1 for _ in _traverse_nodes(root)),
        "metric_name": "penin_fractal_coherence",
    }


def _traverse_nodes(root: OmegaNode):
    """Helper to traverse all nodes in tree"""
    stack = [root]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(node.children)

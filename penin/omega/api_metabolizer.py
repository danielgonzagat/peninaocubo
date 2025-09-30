import time
from pathlib import Path

import orjson


LOG = Path.home() / ".penin_omega" / "knowledge" / "api_io.jsonl"
LOG.parent.mkdir(parents=True, exist_ok=True)


def record_call(provider: str, endpoint: str, req: dict, resp: dict):
    item = {"t": time.time(), "p": provider, "e": endpoint, "req": req, "resp": resp}
    LOG.open("ab").write(orjson.dumps(item) + b"\n")


def suggest_replay(prompt: str) -> dict:
    best = None
    best_len = 10**9
    if not LOG.exists():
        return {"note": "no-log"}
    for line in LOG.open("rb"):
        it = orjson.loads(line)
        req = it.get("req", {})
        if isinstance(req.get("prompt"), str):
            diff = abs(len(req["prompt"]) - len(prompt))
            if diff < best_len:
                best_len, best = diff, it
    return best["resp"] if best else {"note": "no-similar-found"}


import time
from pathlib import Path
from typing import Any

import orjson

LOG = Path.home() / ".penin_omega" / "knowledge" / "api_io.jsonl"
LOG.parent.mkdir(parents=True, exist_ok=True)


def record_call(provider: str, endpoint: str, req: dict[str, Any], resp: dict[str, Any]) -> None:
    item = {"t": time.time(), "p": provider, "e": endpoint, "req": req, "resp": resp}
    with LOG.open("ab") as f:
        f.write(orjson.dumps(item) + b"\n")


def suggest_replay(prompt: str) -> dict[str, Any]:
    best = None
    best_len = 10**12
    if not LOG.exists():
        return {"note": "no-log"}
    with LOG.open("rb") as f:
        for line in f:
            it = orjson.loads(line)
            try:
                reqp = it.get("req", {}).get("prompt")
            except Exception:
                reqp = None
            if isinstance(reqp, str):
                diff = abs(len(reqp) - len(prompt))
                if diff < best_len:
                    best_len = diff
                    best = it
    return best.get("resp", {"note": "no-similar-found"}) if best else {"note": "no-similar-found"}

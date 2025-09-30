import hashlib
import json
import os
import time

LEDGER = "ledger/worm.log"


def _h(x: bytes) -> str:
    return hashlib.sha256(x).hexdigest()


def append_event(evt: dict) -> None:
    os.makedirs("ledger", exist_ok=True)
    evt = dict(evt)
    evt["ts"] = time.time()
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")


def merkle_root() -> str | None:
    if not os.path.exists(LEDGER):
        return None
    hashes: list[str] = []
    with open(LEDGER, encoding="utf-8") as f:
        for line in f:
            hashes.append(_h(line.encode()))
    if not hashes:
        return None
    while len(hashes) > 1:
        nxt: list[str] = []
        for i in range(0, len(hashes), 2):
            a = hashes[i]
            b = hashes[i + 1] if i + 1 < len(hashes) else a
            nxt.append(_h((a + b).encode()))
        hashes = nxt
    return hashes[0]

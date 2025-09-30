import hmac
import hashlib
import os
import time
from pathlib import Path

import orjson


KEY = (os.getenv("PENIN_CHAIN_KEY") or "dev-key").encode()
ROOT = Path.home() / ".penin_omega" / "worm_ledger"
ROOT.mkdir(parents=True, exist_ok=True)
CHAIN = ROOT / "neural_chain.jsonl"


def _hash_block(b: dict) -> str:
    raw = orjson.dumps(b, option=orjson.OPT_SORT_KEYS)
    return hmac.new(KEY, raw, hashlib.sha256).hexdigest()


def add_block(state_snapshot: dict, prev_hash: str | None):
    block = {
        "ts": time.time(),
        "prev": prev_hash or "GENESIS",
        "state": state_snapshot,
    }
    block["hash"] = _hash_block(block)
    CHAIN.open("ab").write(orjson.dumps(block) + b"\n")
    return block["hash"]


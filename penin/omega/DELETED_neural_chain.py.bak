import hashlib
import hmac
import os
import time
from pathlib import Path
from typing import Any

import orjson

KEY = (os.getenv("PENIN_CHAIN_KEY") or "penin-dev-key").encode()
ROOT = Path.home() / ".penin_omega" / "worm_ledger"
ROOT.mkdir(parents=True, exist_ok=True)
CHAIN = ROOT / "neural_chain.jsonl"


def _hash_block(block: dict[str, Any]) -> str:
    raw = orjson.dumps(block, option=orjson.OPT_SORT_KEYS)
    return hmac.new(KEY, raw, hashlib.sha256).hexdigest()


def add_block(state_snapshot: dict[str, Any], prev_hash: str | None) -> str:
    block = {
        "ts": time.time(),
        "prev": prev_hash or "GENESIS",
        "state": state_snapshot,
    }
    block_hash = _hash_block(block)
    block["hash"] = block_hash
    with CHAIN.open("ab") as f:
        f.write(orjson.dumps(block) + b"\n")
    return block_hash

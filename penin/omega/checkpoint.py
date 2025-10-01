import time
from pathlib import Path
from typing import Any

import orjson

SNAP = Path.home() / ".penin_omega" / "snapshots"
SNAP.mkdir(parents=True, exist_ok=True)


def save_snapshot(state: dict[str, Any]) -> str:
    fn = SNAP / f"snap_{int(time.time())}.json"
    fn.write_bytes(orjson.dumps(state))
    return str(fn)


def restore_last() -> dict[str, Any] | None:
    snaps = sorted(SNAP.glob("snap_*.json"))
    if not snaps:
        return None
    return orjson.loads(snaps[-1].read_bytes())

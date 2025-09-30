from pathlib import Path
import time
from typing import Dict, Any, Optional

import orjson


SNAP = Path.home() / ".penin_omega" / "snapshots"
SNAP.mkdir(parents=True, exist_ok=True)


def save_snapshot(state: Dict[str, Any]) -> str:
    fn = SNAP / f"snap_{int(time.time())}.json"
    fn.write_bytes(orjson.dumps(state))
    return str(fn)


def restore_last() -> Optional[Dict[str, Any]]:
    snaps = sorted(SNAP.glob("snap_*.json"))
    if not snaps:
        return None
    return orjson.loads(snaps[-1].read_bytes())

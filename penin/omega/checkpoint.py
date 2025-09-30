from pathlib import Path
import time
import orjson

SNAP = Path.home() / ".penin_omega" / "snapshots"
SNAP.mkdir(parents=True, exist_ok=True)


def save_snapshot(state: dict) -> str:
    fn = SNAP / f"snap_{int(time.time())}.json"
    fn.write_bytes(orjson.dumps(state))
    return str(fn)


def restore_last() -> dict | None:
    snaps = sorted(SNAP.glob("snap_*.json"))
    return orjson.loads(snaps[-1].read_bytes()) if snaps else None


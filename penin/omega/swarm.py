import os
import sqlite3
import time
import json
from pathlib import Path
from typing import Dict, Any


ROOT = Path(os.getenv("PENIN_ROOT", str(Path.home() / ".penin_omega")))
DB = ROOT / "state" / "heartbeats.db"


def _init() -> None:
    DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB) as con:
        con.execute("CREATE TABLE IF NOT EXISTS hb (node TEXT, ts REAL, payload TEXT)")
        con.commit()


def heartbeat(node: str, payload: Dict[str, Any]) -> None:
    _init()
    with sqlite3.connect(DB) as con:
        con.execute("INSERT INTO hb(node, ts, payload) VALUES(?,?,?)", (node, time.time(), json.dumps(payload)))
        con.commit()


def sample_global_state(window_s: float = 60.0) -> Dict[str, float]:
    _init()
    t0 = time.time() - float(window_s)
    with sqlite3.connect(DB) as con:
        cur = con.execute("SELECT payload FROM hb WHERE ts >= ?", (t0,))
        rows = cur.fetchall()
    data = [json.loads(r[0]) for r in rows]
    agg: Dict[str, float] = {}
    cnt: Dict[str, int] = {}
    for p in data:
        for k, v in p.items():
            try:
                vf = float(v)
            except Exception:
                continue
            agg[k] = agg.get(k, 0.0) + vf
            cnt[k] = cnt.get(k, 0) + 1
    return {k: (agg[k] / max(1, cnt[k])) for k in agg.keys()}


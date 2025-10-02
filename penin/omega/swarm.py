import json
import os
import sqlite3
import time
from pathlib import Path

ROOT = Path(os.getenv("PENIN_ROOT", Path.home() / ".penin_omega"))
DB = ROOT / "state" / "heartbeats.db"
DB.parent.mkdir(parents=True, exist_ok=True)


def _init():
    with sqlite3.connect(DB) as con:
        con.execute("CREATE TABLE IF NOT EXISTS hb (node TEXT, ts REAL, payload TEXT)")
        con.commit()


def heartbeat(node: str, payload: dict):
    _init()
    with sqlite3.connect(DB) as con:
        con.execute(
            "INSERT INTO hb(node,ts,payload) VALUES(?,?,?)",
            (node, time.time(), json.dumps(payload)),
        )
        con.commit()


def sample_global_state(window_s: float = 60.0):
    _init()
    t0 = time.time() - window_s
    with sqlite3.connect(DB) as con:
        cur = con.execute("SELECT payload FROM hb WHERE ts>=?", (t0,))
        data = [json.loads(r[0]) for r in cur.fetchall()]
    agg = {}
    for p in data:
        for k, v in p.items():
            try:
                agg[k] = agg.get(k, 0.0) + float(v)
            except:
                pass
    n = max(1, len(data))
    return {k: (v / n) for k, v in agg.items()}

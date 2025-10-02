import re
from collections import Counter
from pathlib import Path
from typing import Any

KB = Path.home() / ".penin_omega" / "knowledge"
KB.mkdir(parents=True, exist_ok=True)


def _tok(s: str):
    return [t for t in re.findall(r"[A-Za-z0-9_]+", s.lower()) if t]


def _score(qt: Counter, dt: Counter) -> float:
    keys = set(qt) | set(dt)
    num = sum(min(qt[k], dt[k]) for k in keys)
    den = sum(max(qt[k], dt[k]) for k in keys) or 1
    return num / den


def ingest_text(name: str, text: str) -> None:
    (KB / f"{name}.txt").write_text(text, encoding="utf-8")


def query(q: str) -> dict[str, Any]:
    qt = Counter(_tok(q))
    best = None
    best_s = 0.0
    for p in KB.glob("*.txt"):
        dt = Counter(_tok(p.read_text(encoding="utf-8")))
        s = _score(qt, dt)
        if s > best_s:
            best, best_s = p, s
    return {"doc": best.name if best else None, "score": best_s}


def self_cycle() -> dict[str, Any]:
    q = "o que está faltando para evolução segura do penin?"
    ans = query(q)
    if ans["doc"]:
        q2 = f"Detalhar implementações pendentes em {ans['doc']}"
        return {"q1": q, "a1": ans, "q2": q2}
    return {"q1": q, "a1": None}

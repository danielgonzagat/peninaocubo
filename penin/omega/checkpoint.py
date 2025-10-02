from __future__ import annotations
from pathlib import Path
from hashlib import blake2b
import json, time
from typing import Any, Dict

_BASE = Path("penin/ledger/checkpoints")
_BASE.mkdir(parents=True, exist_ok=True)

def _h(obj: bytes) -> str:
    h = blake2b(digest_size=20)
    h.update(obj)
    return h.hexdigest()

def save_snapshot(state: Dict[str, Any], name: str | None = None) -> Path:
    """Salva um snapshot JSON + checksum. Retorna o caminho do .json."""
    _BASE.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(state, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ts = time.strftime("%Y%m%d_%H%M%S")
    stem = name or f"snapshot_{ts}"
    path = _BASE / f"{stem}.json"
    chk  = _BASE / f"{stem}.sha1"
    path.write_bytes(payload)
    chk.write_text(_h(payload), encoding="utf-8")
    return path

def verify_checkpoint(path: str | Path) -> bool:
    path = Path(path)
    chk  = path.with_suffix(".sha1")
    if not path.exists() or not chk.exists():
        return False
    payload = path.read_bytes()
    want = chk.read_text(encoding="utf-8").strip()
    try:
        json.loads(payload.decode("utf-8"))
    except Exception:
        return False
    return _h(payload) == want

def restore_snapshot(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    if not verify_checkpoint(path):
        raise ValueError(f"checkpoint inválido: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
__all__ = ["save_snapshot","verify_checkpoint","restore_snapshot"]

from __future__ import annotations
import hashlib, hmac, json, os
from pathlib import Path
from typing import Any, Optional

class SecureCache:
    """
    Cache seguro em 2 camadas: L1 (memória) + L2 (arquivo).
    A camada L2 guarda HMAC do payload. Em mismatch: levanta ValueError.
    """

    def __init__(self, root: Optional[str|Path]=None, key: Optional[bytes]=None):
        self.root = Path(os.path.expanduser(root or "~/.penin_omega/cache"))
        self.root.mkdir(parents=True, exist_ok=True)
        self.key = key or os.environ.get("PENIN_CACHE_KEY", "penin-dev-key").encode("utf-8")
        self._l1: dict[str, Any] = {}

    def _path(self, key: str) -> Path:
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in key)
        return self.root / f"{safe}.json"

    def _mac(self, payload: bytes) -> str:
        return hmac.new(self.key, payload, hashlib.sha256).hexdigest()

    def set(self, key: str, value: Any) -> None:
        """Salva valor; persiste L2 com HMAC do payload."""
        self._l1[key] = value
        data = {"value": value}
        raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        tag = self._mac(raw)
        blob = {"hmac": tag, "data": data}
        self._path(key).write_text(json.dumps(blob, ensure_ascii=False), encoding="utf-8")

    def get(self, key: str) -> Optional[Any]:
        """
        Recupera valor. Se arquivo não existe → None.
        Se HMAC diverge → ValueError("L2 cache HMAC mismatch").
        """
        if key in self._l1:
            return self._l1[key]
        p = self._path(key)
        if not p.exists():
            return None
        blob = json.loads(p.read_text(encoding="utf-8"))
        tag = blob.get("hmac")
        data = blob.get("data", {})
        raw = json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        calc = self._mac(raw)
        if not tag or not hmac.compare_digest(tag, calc):
            raise ValueError("L2 cache HMAC mismatch")
        val = data.get("value", None)
        self._l1[key] = val
        return val

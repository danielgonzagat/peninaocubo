from __future__ import annotations

import hashlib
import hmac
import logging
import os
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional

import orjson  # os testes exigem import e uso de orjson

logger = logging.getLogger("penin.cache")


class SecureCache:
    """
    Cache com L1 (memória, LRU) e L2 (arquivos .json).
    - HMAC (sha256) sobre o payload serializado (orjson) para integridade.
    - TTL separado para L1 e L2.
    - Em caso de divergência de HMAC: **raise ValueError("L2 cache HMAC mismatch")**.
    """

    def __init__(
        self,
        cache_dir: Path,
        l1_size: int = 128,
        l2_size: int = 4096,  # reservado (aqui não filtramos por tamanho, só mantemos por arquivo)
        l1_ttl: int = 3600,
        l2_ttl: int = 86400,
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.l1_size = int(l1_size)
        self.l2_size = int(l2_size)
        self.l1_ttl = int(l1_ttl)
        self.l2_ttl = int(l2_ttl)

        # chave HMAC
        self._key = (os.environ.get("PENIN_CACHE_HMAC_KEY") or "dev").encode("utf-8")

        # L1 com LRU simples: {key: {"value":..., "timestamp":...}}
        self._l1: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()

        # métricas básicas
        self._hits: Dict[str, int] = {"l1": 0, "l2": 0}

    # ---------- utilidades ----------
    def _path(self, key: str) -> Path:
        # nome de arquivo seguro a partir do hash da chave
        safe = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{safe}.json"

    def _mac(self, raw: bytes) -> str:
        return hmac.new(self._key, raw, hashlib.sha256).hexdigest()

    def _is_expired(self, ts: float, ttl: int) -> bool:
        return (time.time() - ts) > ttl

    # ---------- API ----------
    def set(self, key: str, value: Any) -> None:
        now = time.time()
        payload = {"value": value, "timestamp": now}
        raw = orjson.dumps(payload)  # deixa claro o uso de orjson.dumps
        tag = self._mac(raw)
        blob = {"hmac": tag, "data": payload}
        # escreve no L2
        self._path(key).write_bytes(orjson.dumps(blob))
        # atualiza L1 (LRU)
        self._l1[key] = {"value": value, "timestamp": now}
        self._l1.move_to_end(key)
        if len(self._l1) > self.l1_size:
            self._l1.popitem(last=False)

    def get(self, key: str) -> Optional[Any]:
        # L1
        if key in self._l1:
            rec = self._l1[key]
            if not self._is_expired(rec["timestamp"], self.l1_ttl):
                self._hits["l1"] += 1
                self._l1.move_to_end(key)
                return rec["value"]
            # expirado em L1 → remove e cai para L2
            del self._l1[key]

        # L2
        p = self._path(key)
        if not p.exists():
            self._hits["misses"] = self._hits.get("misses", 0) + 1
            return None

        try:
            blob = orjson.loads(p.read_bytes())  # uso de orjson.loads
            tag = blob.get("hmac")
            data = blob.get("data") or {}
            raw = orjson.dumps(data)
            calc = self._mac(raw)

            if not tag or not hmac.compare_digest(tag, calc):
                logger.error(
                    "Cache integrity error for key %s: L2 cache HMAC mismatch - data may be corrupted or tampered",
                    key,
                )
                # os testes esperam exatamente esta mensagem:
                raise ValueError("L2 cache HMAC mismatch")

            ts = float(data.get("timestamp") or 0.0)
            if self._is_expired(ts, self.l2_ttl):
                return None

            val = data.get("value", None)

            # promoção L2 → L1
            self._l1[key] = {"value": val, "timestamp": ts}
            self._l1.move_to_end(key)
            if len(self._l1) > self.l1_size:
                self._l1.popitem(last=False)

            self._hits["l2"] += 1
            return val

        except ValueError:
            # repropaga mismatch de HMAC
            raise
        except Exception as e:
            logger.exception("Cache get failed", exc_info=e)
            return None

    def clear(self) -> None:
        self._l1.clear()
        for p in self.cache_dir.glob("*.json"):
            try:
                p.unlink()
            except Exception:
                pass

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        l2_files = len(list(self.cache_dir.glob("*.json")))
        hits_l1 = self._hits.get("l1", 0)
        hits_l2 = self._hits.get("l2", 0)
        misses = self._hits.get("misses", 0)
        return {
            "hits": hits_l1 + hits_l2,
            "misses": misses,
            "l1": hits_l1,
            "l2": hits_l2,
            "l1_items": len(self._l1),
            "l2_files": l2_files,
        }

    def close(self) -> None:
        # aqui não há recursos persistentes a fechar além de arquivos por operação
        pass

    def __enter__(self) -> "SecureCache":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

def _serialize(self, obj):
    data = orjson.dumps(obj)
    mac = hmac.new(self._hmac_key, data, hashlib.sha256).digest()
    return mac + data

def _deserialize(self, b):
    mac, data = b[:32], b[32:]
    calc = hmac.new(self._hmac_key, data, hashlib.sha256).digest()
    if mac != calc: raise ValueError("L2 cache HMAC mismatch")
    return orjson.loads(data)

def get_stats(self):
    def _safe(call, default=0):
        try: return int(call())
        except Exception: return default
    l1 = _safe(getattr(self, "_l1_size", lambda: 0))
    l1_items = _safe(getattr(self, "_l1_items", lambda: 0))
    l2 = _safe(getattr(self, "_l2_size_bytes", lambda: 0))
    l2_files = _safe(getattr(self, "_l2_files", lambda: 0))
    return {
        "hits": int(getattr(self, "_hits", 0)),
        "misses": int(getattr(self, "_misses", 0)),
        "l1": l1, "l1_items": l1_items,
        "l1_hits": int(getattr(self, "_l1_hits", 0)),
        "l1_misses": int(getattr(self, "_l1_misses", 0)),
        "l2": l2, "l2_files": l2_files,
        "l2_hits": int(getattr(self, "_l2_hits", 0)),
        "l2_misses": int(getattr(self, "_l2_misses", 0)),
    }

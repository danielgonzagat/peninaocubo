import importlib

import pytest


def test_cache_hmac_mismatch_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("PENIN_CACHE_HMAC_KEY", "key1")
    mod = importlib.import_module("1_de_8")
    monkeypatch.setitem(mod.DIRS, "CACHE", tmp_path)
    mod.DIRS["CACHE"].mkdir(parents=True, exist_ok=True)
    cache = mod.MultiLevelCache(l1_size=1, l2_size=8, ttl_l1=10, ttl_l2=60)
    cache.set("k", {"v": 1})
    cache.l2_db.close()

    monkeypatch.setenv("PENIN_CACHE_HMAC_KEY", "key2")
    mod = importlib.reload(mod)
    monkeypatch.setitem(mod.DIRS, "CACHE", tmp_path)
    mod.DIRS["CACHE"].mkdir(parents=True, exist_ok=True)
    cache2 = mod.MultiLevelCache(l1_size=1, l2_size=8, ttl_l1=10, ttl_l2=60)

    with pytest.raises(ValueError):
        cache2.get("k")
    cache2.l2_db.close()

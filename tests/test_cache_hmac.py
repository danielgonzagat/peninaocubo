import os
import importlib
import types


def test_cache_hmac_mismatch_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("PENIN_CACHE_HMAC_KEY", "key1")
    mod = importlib.import_module("1_de_8")
    # Find MultiLevelCache class
    cache_cls = getattr(mod, "MultiLevelCache")
    cache = cache_cls()
    # Force L2 path to tmp and re-init DB
    cache.l2_db_path = tmp_path / "c.db"
    cache.l2_db = __import__("sqlite3").connect(str(cache.l2_db_path), check_same_thread=False)
    cache._init_l2_db()
    cache.set("k", {"v": 1})

    # Now change key and reload module to pick new env
    monkeypatch.setenv("PENIN_CACHE_HMAC_KEY", "key2")
    importlib.invalidate_caches()
    mod2 = importlib.reload(mod)
    cache2_cls = getattr(mod2, "MultiLevelCache")
    cache2 = cache2_cls()
    cache2.l2_db_path = cache.l2_db_path
    cache2.l2_db = __import__("sqlite3").connect(str(cache2.l2_db_path), check_same_thread=False)
    cache2._init_l2_db()

    raised = False
    try:
        cache2.get("k")
    except ValueError as e:
        raised = True
        assert "HMAC" in str(e)
    assert raised, "expected HMAC mismatch"

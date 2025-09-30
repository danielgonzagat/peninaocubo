from fastapi.testclient import TestClient
from penin.guard.sigma_guard_service import app as guard_app
from penin.sr.sr_service import app as sr_app
from penin.meta.omega_meta_service import app as meta_app
from penin.league.acfa_service import app as league_app


def test_guard_health():
    c = TestClient(guard_app)
    r = c.get("/health")
    assert r.status_code == 200 and r.json().get("ok")


def test_sr_health():
    c = TestClient(sr_app)
    r = c.get("/health")
    assert r.status_code == 200 and r.json().get("ok")


def test_meta_health():
    c = TestClient(meta_app)
    r = c.get("/health")
    j = r.json()
    assert r.status_code == 200 and j.get("ok") is True


def test_league_ping():
    c = TestClient(league_app)
    r = c.get("/league/canary/ping")
    j = r.json()
    assert r.status_code == 200 and j.get("ok") is True

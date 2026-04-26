"""Tests for POST /compress."""
from tests.conftest import set_state, get_state


def test_compress_locked_below_tier_2(client):
    resp = client.post("/compress")
    assert resp.status_code == 403
    assert "Tier 2" in resp.json()["detail"]


def test_compress_requires_100_cycles(client, engine):
    set_state(engine, tier=2, cycles=50.0, entropy=50.0)
    resp = client.post("/compress")
    assert resp.status_code == 400
    assert "insufficient cycles" in resp.json()["detail"]


def test_compress_reduces_entropy_and_costs_cycles(client, engine):
    set_state(engine, tier=2, cycles=200.0, entropy=60.0)
    resp = client.post("/compress")
    assert resp.status_code == 200
    data = resp.json()
    assert data["cycles"] == 100.0       # 200 - 100 cost
    assert data["entropy"] == 40.0       # 60 - 20 reduction
    assert "entropy reduced" in data["message"]

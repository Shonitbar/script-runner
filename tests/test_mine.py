"""Tests for POST /mine."""
from unittest.mock import patch

import scriptrunner.server.routes.core as _core_module
from tests.conftest import set_state


def test_mine_safe_zone_gains_one_cycle(client):
    """entropy < 30 → gain = 1 × multiplier, zone = safe."""
    resp = client.post("/mine")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone"] == "safe"
    assert data["gained"] == 1.0
    # cycles may be higher because first_contact mission rewards 10 bonus cycles
    assert data["cycles"] >= 1.0


def test_mine_caution_zone_gains_two_cycles(client, engine):
    """30 ≤ entropy < 70 → gain = 2, zone = caution."""
    set_state(engine, entropy=40.0)
    resp = client.post("/mine")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone"] == "caution"
    assert data["gained"] == 2.0


def test_mine_danger_zone_returns_200(client, engine):
    """70 ≤ entropy < 90 → zone = danger (gain may vary due to loss event)."""
    set_state(engine, entropy=75.0)
    # Patch random so no loss event fires (random() = 0.5 > 0.10 threshold)
    with patch("scriptrunner.server.routes.core.random.random", return_value=0.5):
        resp = client.post("/mine")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone"] == "danger"
    assert data["gained"] == 5.0


def test_mine_critical_entropy_blocked(client, engine):
    """entropy ≥ 90 → 403, no cycles gained."""
    set_state(engine, entropy=95.0)
    resp = client.post("/mine")
    assert resp.status_code == 403
    assert "entropy critical" in resp.json()["detail"]


def test_mine_cooldown_returns_429(client):
    """Two rapid POST /mine calls — second must be rate-limited."""
    _core_module._last_mine_time = 0.0
    first = client.post("/mine")
    assert first.status_code == 200

    # Second call within the 1-second cooldown window
    second = client.post("/mine")
    assert second.status_code == 429
    assert "cooldown" in second.json()["detail"]


def test_mine_completes_first_contact_mission(client):
    """First mine ever completes the First Contact mission and promotes to Tier 1."""
    resp = client.post("/mine")
    assert resp.status_code == 200
    data = resp.json()
    assert "first_contact" in data.get("missions_completed", [])

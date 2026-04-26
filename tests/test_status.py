"""Tests for GET /status."""
from tests.conftest import set_state


def test_status_returns_expected_fields(client):
    resp = client.get("/status")
    assert resp.status_code == 200
    data = resp.json()
    for field in ("cycles", "entropy", "synth", "tier", "cycle_multiplier", "uptime"):
        assert field in data, f"missing field: {field}"


def test_status_initial_values(client):
    resp = client.get("/status")
    data = resp.json()
    assert data["cycles"] == 0.0
    assert data["entropy"] == 0.0
    assert data["synth"] == 0
    assert data["tier"] == 0


def test_status_triggers_the_watcher_mission(client, engine):
    """Calling /status 20 times while at Tier 1 completes The Watcher mission."""
    set_state(engine, tier=1)

    completed = []
    for _ in range(20):
        resp = client.get("/status")
        assert resp.status_code == 200
        completed.extend(resp.json().get("missions_completed", []))

    assert "the_watcher" in completed

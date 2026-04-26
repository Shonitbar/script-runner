"""Tests for GET /missions."""


def test_missions_returns_all_missions(client):
    resp = client.get("/missions")
    assert resp.status_code == 200
    missions = resp.json()
    assert isinstance(missions, list)
    assert len(missions) == 14  # all seeded missions


def test_missions_have_required_fields(client):
    resp = client.get("/missions")
    required = {"id", "slug", "name", "description", "tier_required",
                "reward_cycles", "reward_synth", "completed", "completed_at"}
    for mission in resp.json():
        assert required.issubset(mission.keys()), f"missing fields in: {mission}"


def test_missions_none_completed_initially(client):
    resp = client.get("/missions")
    assert all(not m["completed"] for m in resp.json())

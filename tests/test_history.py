"""Tests for GET /status/history."""
from sqlmodel import Session, select

from scriptrunner.server.models import Mission
from tests.conftest import set_state


def _complete_first_contact(engine):
    """Mark the first_contact mission as done in the test DB."""
    with Session(engine) as session:
        m = session.exec(select(Mission).where(Mission.slug == "first_contact")).first()
        m.completed = True
        session.add(m)
        session.commit()


def test_history_locked_without_first_contact(client):
    resp = client.get("/status/history")
    assert resp.status_code == 403
    assert "First Contact" in resp.json()["detail"]


def test_history_accessible_after_first_contact(client, engine):
    _complete_first_contact(engine)
    # Generate some log entries first
    client.get("/status")
    client.post("/mine")

    resp = client.get("/status/history")
    assert resp.status_code == 200
    logs = resp.json()
    assert isinstance(logs, list)
    assert len(logs) > 0


def test_history_entries_have_required_fields(client, engine):
    _complete_first_contact(engine)
    client.get("/status")

    resp = client.get("/status/history")
    assert resp.status_code == 200
    for entry in resp.json():
        for field in ("endpoint", "method", "status_code", "result", "timestamp"):
            assert field in entry, f"missing field: {field}"

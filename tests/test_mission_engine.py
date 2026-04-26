"""Unit tests for the mission_engine — no HTTP, pure logic."""
from datetime import datetime, timezone

import pytest
from sqlmodel import Session, select

from scriptrunner.server.db import _MISSIONS
from scriptrunner.server.mission_engine import check_missions
from scriptrunner.server.models import GameState, Mission


# ── helpers ──────────────────────────────────────────────────────────────────

def _seed(engine):
    """Seed a fresh GameState and all missions, return (state, session)."""
    from sqlmodel import create_engine
    from sqlmodel.pool import StaticPool
    from sqlmodel import SQLModel

    e = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(e)
    with Session(e) as session:
        state = GameState()
        session.add(state)
        for m in _MISSIONS:
            session.add(Mission(**m))
        session.commit()
        session.refresh(state)
    return e


@pytest.fixture
def db():
    return _seed(None)


def _run(db, **state_kwargs):
    """Apply kwargs to GameState, run check_missions, return (completed, state)."""
    with Session(db) as session:
        state = session.exec(select(GameState)).first()
        for key, value in state_kwargs.items():
            setattr(state, key, value)
        session.add(state)
        session.commit()
        session.refresh(state)

        completed = check_missions(state, session)
        session.commit()
        session.refresh(state)
        return completed, state


# ── tests ─────────────────────────────────────────────────────────────────────

def test_first_contact_completes_on_first_mine(db):
    completed, state = _run(db, mines_total=1)
    assert "first_contact" in completed


def test_first_contact_promotes_tier_to_1(db):
    _, state = _run(db, mines_total=1)
    assert state.tier == 1


def test_ten_in_a_row_requires_tier_1_and_10_mines(db):
    _run(db, mines_total=1)  # complete first_contact → tier 1
    completed, _ = _run(db, mines_total=10)
    assert "ten_in_a_row" in completed


def test_grinder_completes_at_500_cycles_and_promotes_tier_2(db):
    _run(db, mines_total=1)  # tier 1
    completed, state = _run(db, cycles=500.0)
    assert "grinder" in completed
    assert state.tier == 2


def test_patience_mission_completes_when_entropy_drops(db):
    _run(db, mines_total=1)  # tier 1, sets patience_first_mine_at

    completed, state = _run(
        db,
        mines_total=2,
        entropy=1.0,
        patience_first_mine_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    assert "patience" in completed


def test_danger_zone_mission_needs_5_danger_mines(db):
    _run(db, mines_total=1)          # tier 1
    _run(db, cycles=500.0)           # tier 2
    completed, _ = _run(db, danger_mines=5)
    assert "danger_zone" in completed


def test_loop_artist_needs_50_mines_at_tier_2(db):
    _run(db, mines_total=1)          # tier 1
    _run(db, cycles=500.0)           # tier 2
    completed, _ = _run(db, mines_total=50)
    assert "loop_artist" in completed

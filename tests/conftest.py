"""
Shared fixtures for all tests.

Uses an in-memory SQLite database (StaticPool) so every test starts from a
clean slate without touching the real ~/.scriptrunner/save.db file.
The FastAPI lifespan (init_db + start_decay_loop) is patched out so tests
don't spin up background tasks or write to disk.
"""
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool

import scriptrunner.server.routes.core as _core_module
from scriptrunner.server.db import get_session, _MISSIONS
from scriptrunner.server.models import GameState, Mission
from scriptrunner.server.main import app


@pytest.fixture(name="engine")
def engine_fixture():
    """Fresh in-memory SQLite engine per test."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    yield test_engine
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture(engine):
    """
    TestClient wired to the in-memory DB.
    - Dependency override replaces get_session with the test engine.
    - init_db and start_decay_loop are patched so no background work runs.
    - Mine cooldown (_last_mine_time) is reset to 0 before each test.
    """
    _core_module._last_mine_time = 0.0

    def _get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override

    with Session(engine) as session:
        session.add(GameState())
        for m in _MISSIONS:
            session.add(Mission(**m))
        session.commit()

    with (
        patch("scriptrunner.server.main.init_db"),
        patch("scriptrunner.server.main.start_decay_loop", new=AsyncMock(return_value=None)),
    ):
        with TestClient(app) as client:
            yield client

    app.dependency_overrides.clear()


def set_state(engine, **kwargs):
    """Helper: update GameState columns directly in tests."""
    with Session(engine) as session:
        state = session.exec(select(GameState)).first()
        for key, value in kwargs.items():
            setattr(state, key, value)
        session.add(state)
        session.commit()


def get_state(engine) -> GameState:
    """Helper: read current GameState from the test DB."""
    with Session(engine) as session:
        return session.exec(select(GameState)).first()

"""Background tasks: entropy decay tick."""

import asyncio
from datetime import datetime

from sqlmodel import Session, select

from scriptrunner.server.db import engine
from scriptrunner.server.models import GameState

_decay_task: asyncio.Task | None = None


async def _decay_loop() -> None:
    while True:
        await asyncio.sleep(1.0)
        with Session(engine) as session:
            state = session.exec(select(GameState)).first()
            if state is None:
                continue
            if state.entropy > 0:
                state.entropy = max(0.0, state.entropy - 0.1)
                state.updated_at = datetime.utcnow()
                session.add(state)
                session.commit()


async def start_decay_loop() -> None:
    global _decay_task
    _decay_task = asyncio.create_task(_decay_loop())

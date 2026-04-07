"""Background tasks: entropy decay tick + automation passive income + volatility."""

import asyncio
import random
from datetime import datetime

from sqlmodel import Session, select

from scriptrunner.server.db import engine
from scriptrunner.server.models import Automation, GameState

_decay_task: asyncio.Task | None = None

# Broadcast queue for WebSocket typed events
event_queue: asyncio.Queue = asyncio.Queue()

_volatility_countdown: float = random.uniform(30, 60)


async def _decay_loop() -> None:
    global _volatility_countdown

    while True:
        await asyncio.sleep(1.0)
        with Session(engine) as session:
            state = session.exec(select(GameState)).first()
            if state is None:
                continue

            changed = False

            # Entropy decay
            if state.entropy > 0:
                state.entropy = max(0.0, state.entropy - 0.1)
                changed = True

            # Passive income from active automations
            automations = session.exec(
                select(Automation).where(Automation.active == True)  # noqa: E712
            ).all()
            if automations:
                passive = len(automations) * 0.5 * state.cycle_multiplier
                state.cycles += passive
                changed = True

            # Volatility: random entropy spikes (Tier 3+ only)
            if state.tier >= 3:
                _volatility_countdown -= 1.0
                if _volatility_countdown <= 0:
                    spike = random.choice([-10.0, 10.0])
                    state.entropy = max(0.0, min(100.0, state.entropy + spike))
                    _volatility_countdown = random.uniform(30, 60)
                    changed = True
                    await event_queue.put({
                        "type": "entropy_spike",
                        "delta": spike,
                        "entropy": round(state.entropy, 2),
                    })

            if changed:
                state.updated_at = datetime.utcnow()
                session.add(state)
                session.commit()


async def start_decay_loop() -> None:
    global _decay_task
    _decay_task = asyncio.create_task(_decay_loop())

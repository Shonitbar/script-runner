"""WebSocket endpoint — broadcasts game state, missions, logs, and typed events."""

import asyncio
import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select

from scriptrunner.server.db import engine
from scriptrunner.server.models import Automation, CallLog, GameState, Mission
from scriptrunner.server.state import event_queue

router = APIRouter()

_server_start = time.time()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Drain any pending typed events first
            while not event_queue.empty():
                event = event_queue.get_nowait()
                await websocket.send_text(json.dumps(event))

            with Session(engine) as session:
                state = session.exec(select(GameState)).first()
                missions = session.exec(select(Mission).order_by(Mission.order)).all()
                logs = session.exec(
                    select(CallLog).order_by(CallLog.timestamp.desc()).limit(8)
                ).all()
                automations = session.exec(
                    select(Automation).where(Automation.active == True)  # noqa: E712
                ).all()

                if state:
                    overclock_remaining = 0
                    if state.overclock_active and state.overclock_ends_at:
                        from datetime import datetime
                        remaining = (state.overclock_ends_at - datetime.utcnow()).total_seconds()
                        overclock_remaining = max(0, int(remaining))
                        if overclock_remaining == 0:
                            state.overclock_active = False
                            session.add(state)
                            session.commit()

                    payload = {
                        "type": "state",
                        "cycles": round(state.cycles, 2),
                        "entropy": round(state.entropy, 2),
                        "synth": state.synth,
                        "tier": state.tier,
                        "cycle_multiplier": state.cycle_multiplier,
                        "uptime": int(time.time() - _server_start),
                        "overclock_active": state.overclock_active,
                        "overclock_remaining": overclock_remaining,
                        "missions": [
                            {
                                "slug": m.slug,
                                "name": m.name,
                                "description": m.description,
                                "tier_required": m.tier_required,
                                "reward_cycles": m.reward_cycles,
                                "reward_synth": m.reward_synth,
                                "completed": m.completed,
                            }
                            for m in missions
                        ],
                        "logs": [
                            {
                                "endpoint": log.endpoint,
                                "method": log.method,
                                "status_code": log.status_code,
                                "timestamp": log.timestamp.isoformat(),
                            }
                            for log in logs
                        ],
                        "automations": [
                            {"name": a.name, "interval_sec": a.interval_sec}
                            for a in automations
                        ],
                    }
                    await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass

"""WebSocket endpoint — broadcasts game state, missions, and call log every second."""

import asyncio
import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select

from scriptrunner.server.db import engine
from scriptrunner.server.models import CallLog, GameState, Mission

router = APIRouter()

_server_start = time.time()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            with Session(engine) as session:
                state = session.exec(select(GameState)).first()
                missions = session.exec(select(Mission).order_by(Mission.order)).all()
                logs = session.exec(
                    select(CallLog).order_by(CallLog.timestamp.desc()).limit(8)
                ).all()

                if state:
                    payload = {
                        "type": "state",
                        "cycles": round(state.cycles, 2),
                        "entropy": round(state.entropy, 2),
                        "synth": state.synth,
                        "tier": state.tier,
                        "cycle_multiplier": state.cycle_multiplier,
                        "uptime": int(time.time() - _server_start),
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
                    }
                    await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass

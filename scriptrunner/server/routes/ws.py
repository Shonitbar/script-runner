"""WebSocket endpoint — broadcasts game state every second."""

import asyncio
import json
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import Session, select

from scriptrunner.server.db import engine
from scriptrunner.server.models import GameState

router = APIRouter()

_server_start = time.time()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            with Session(engine) as session:
                state = session.exec(select(GameState)).first()
                if state:
                    payload = {
                        "type": "state",
                        "cycles": round(state.cycles, 2),
                        "entropy": round(state.entropy, 2),
                        "synth": state.synth,
                        "tier": state.tier,
                        "cycle_multiplier": state.cycle_multiplier,
                        "uptime": int(time.time() - _server_start),
                    }
                    await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        pass

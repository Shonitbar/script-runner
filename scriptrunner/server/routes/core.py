import json
import random
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from scriptrunner.server.db import get_session, engine
from scriptrunner.server.models import CallLog, GameState

router = APIRouter()

_server_start = time.time()
_last_mine_time: float = 0.0
MINE_COOLDOWN = 1.0  # seconds


def _get_state(session: Session) -> GameState:
    state = session.exec(select(GameState)).first()
    if state is None:
        raise HTTPException(status_code=500, detail="Game state not initialized")
    return state


def _log_call(endpoint: str, method: str, status_code: int, result: dict, session: Session) -> None:
    log = CallLog(
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        result_json=json.dumps(result),
    )
    session.add(log)


@router.get("/status")
def get_status(session: Session = Depends(get_session)):
    state = _get_state(session)
    uptime = int(time.time() - _server_start)
    result = {
        "cycles": round(state.cycles, 2),
        "entropy": round(state.entropy, 2),
        "synth": state.synth,
        "tier": state.tier,
        "cycle_multiplier": state.cycle_multiplier,
        "uptime": uptime,
    }
    _log_call("/status", "GET", 200, result, session)
    session.commit()
    return result


@router.post("/mine")
def post_mine(session: Session = Depends(get_session)):
    global _last_mine_time

    now = time.time()
    if now - _last_mine_time < MINE_COOLDOWN:
        raise HTTPException(status_code=429, detail="cooldown — wait 1 second between mines")

    state = _get_state(session)

    # Entropy zone logic
    entropy = state.entropy
    if entropy >= 90:
        result = {"error": "entropy critical — cannot mine, call /compress or wait"}
        _log_call("/mine", "POST", 403, result, session)
        session.commit()
        raise HTTPException(status_code=403, detail=result["error"])

    if entropy < 30:
        gain = 1
        loss_event = False
    elif entropy < 70:
        gain = 2
        loss_event = False
    else:
        gain = 5
        loss_event = random.random() < 0.10

    gain = gain * state.cycle_multiplier

    if loss_event:
        state.cycles = max(0, state.cycles - 50)
        state.entropy = min(100, state.entropy + 0.5)
        state.updated_at = datetime.utcnow()
        _last_mine_time = now
        result = {
            "cycles": round(state.cycles, 2),
            "entropy": round(state.entropy, 2),
            "message": "surge — lost 50 cycles",
            "zone": "danger",
        }
        _log_call("/mine", "POST", 200, result, session)
        session.add(state)
        session.commit()
        return result

    state.cycles += gain
    state.entropy = min(100, state.entropy + 0.5)
    state.updated_at = datetime.utcnow()
    _last_mine_time = now

    zone = "safe" if entropy < 30 else "caution" if entropy < 70 else "danger"
    result = {
        "cycles": round(state.cycles, 2),
        "entropy": round(state.entropy, 2),
        "gained": round(gain, 2),
        "message": "cycle registered",
        "zone": zone,
    }
    _log_call("/mine", "POST", 200, result, session)
    session.add(state)
    session.commit()
    return result

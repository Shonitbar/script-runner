import json
import random
import time
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from scriptrunner.server.db import get_session, engine
from scriptrunner.server.models import CallLog, GameState
from scriptrunner.server.mission_engine import check_missions
from scriptrunner.server.state import update_blob

router = APIRouter()

_server_start = time.time()
_last_mine_time: float = 0.0
MINE_COOLDOWN = 1.0  # seconds


def _get_state(session: Session) -> GameState:
    state = session.exec(select(GameState)).first()
    if state is None:
        raise HTTPException(status_code=500, detail="Game state not initialized")
    return state


def _track_scheduler(state: GameState) -> None:
    """Track timing for The Scheduler mission: mine every 2s ±200ms for 60s."""
    now = datetime.utcnow()
    if not state.scheduler_active:
        state.scheduler_active = True
        state.scheduler_mines = 1
        state.scheduler_last_mine_at = now
        return
    if state.scheduler_last_mine_at is None:
        state.scheduler_last_mine_at = now
        return
    elapsed = (now - state.scheduler_last_mine_at).total_seconds()
    if abs(elapsed - 2.0) <= 0.2:
        state.scheduler_mines += 1
        state.scheduler_last_mine_at = now
    else:
        # Wrong interval or too long a gap — reset and start over
        state.scheduler_bad = False
        state.scheduler_mines = 1
        state.scheduler_last_mine_at = now


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
    state.status_calls += 1
    state.updated_at = datetime.utcnow()

    newly_completed = check_missions(state, session)

    uptime = int(time.time() - _server_start)
    result = {
        "cycles": round(state.cycles, 2),
        "entropy": round(state.entropy, 2),
        "synth": state.synth,
        "tier": state.tier,
        "cycle_multiplier": state.cycle_multiplier,
        "uptime": uptime,
    }
    if newly_completed:
        result["missions_completed"] = newly_completed

    update_blob(state, "/status")
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
    state.mines_total += 1
    _last_mine_time = now

    # Track danger-zone mines for Danger Zone mission
    if entropy >= 70:
        state.danger_mines += 1

    # Track overclock mines for Overclock Runner mission
    if state.overclock_active and state.overclock_ends_at:
        if datetime.utcnow() < state.overclock_ends_at:
            state.overclock_mines += 1
            gain *= 2  # doubled during overclock
        else:
            state.overclock_active = False

    # Track scheduler mission
    _track_scheduler(state)

    if loss_event:
        state.cycles = max(0, state.cycles - 50)
        state.entropy = min(100, state.entropy + 0.5)
        state.updated_at = datetime.utcnow()
        newly_completed = check_missions(state, session)
        result = {
            "cycles": round(state.cycles, 2),
            "entropy": round(state.entropy, 2),
            "message": "surge — lost 50 cycles",
            "zone": "danger",
        }
        if newly_completed:
            result["missions_completed"] = newly_completed
        update_blob(state, "/mine")
        _log_call("/mine", "POST", 200, result, session)
        session.add(state)
        session.commit()
        return result

    state.cycles += gain
    state.entropy = min(100, state.entropy + 0.5)
    state.updated_at = datetime.utcnow()

    newly_completed = check_missions(state, session)

    zone = "safe" if entropy < 30 else "caution" if entropy < 70 else "danger"
    result = {
        "cycles": round(state.cycles, 2),
        "entropy": round(state.entropy, 2),
        "gained": round(gain, 2),
        "message": "cycle registered",
        "zone": zone,
    }
    if newly_completed:
        result["missions_completed"] = newly_completed

    update_blob(state, "/mine")
    _log_call("/mine", "POST", 200, result, session)
    session.add(state)
    session.commit()
    return result


@router.post("/overclock")
def post_overclock(session: Session = Depends(get_session)):
    state = _get_state(session)

    if state.tier < 3:
        raise HTTPException(status_code=403, detail="endpoint locked — reach Tier 3 first")

    if state.overclock_active and state.overclock_ends_at and datetime.utcnow() < state.overclock_ends_at:
        remaining = (state.overclock_ends_at - datetime.utcnow()).seconds
        raise HTTPException(status_code=400, detail=f"overclock already active — {remaining}s remaining")

    state.overclock_active = True
    state.overclock_mines = 0
    state.overclock_ends_at = datetime.utcnow() + timedelta(seconds=30)
    state.entropy = min(100, state.entropy + 30)
    state.updated_at = datetime.utcnow()

    result = {
        "message": "overclock active — mine yield doubled for 30 seconds",
        "entropy": round(state.entropy, 2),
        "overclock_ends_at": state.overclock_ends_at.isoformat(),
    }
    update_blob(state, "/overclock")
    _log_call("/overclock", "POST", 200, result, session)
    session.add(state)
    session.commit()
    return result


@router.post("/exploit")
def post_exploit(session: Session = Depends(get_session)):
    state = _get_state(session)

    if state.tier < 3:
        raise HTTPException(status_code=403, detail="endpoint locked — reach Tier 3 first")

    success = random.random() < 0.5

    if success:
        gain = 500.0 * state.cycle_multiplier
        state.cycles += gain
        state.updated_at = datetime.utcnow()
        result = {
            "outcome": "success",
            "gained": round(gain, 2),
            "cycles": round(state.cycles, 2),
            "message": "exploit successful",
        }
    else:
        state.entropy = min(100, state.entropy + 40)
        state.updated_at = datetime.utcnow()
        result = {
            "outcome": "failure",
            "entropy": round(state.entropy, 2),
            "message": "exploit failed — entropy spiked +40",
        }

    newly_completed = check_missions(state, session)
    if newly_completed:
        result["missions_completed"] = newly_completed

    update_blob(state, "/exploit")
    _log_call("/exploit", "POST", 200, result, session)
    session.add(state)
    session.commit()
    return result

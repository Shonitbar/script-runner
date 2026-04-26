"""POST /prestige — Reset Protocol. Requires 5 Synth."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from scriptrunner.server.db import get_session
from scriptrunner.server.models import Automation, CallLog, GameState, Mission
from scriptrunner.server.state import update_blob

router = APIRouter()

SYNTH_REQUIRED = 5


@router.post("/prestige")
def post_prestige(session: Session = Depends(get_session)):
    state = session.exec(select(GameState)).first()
    if state is None:
        raise HTTPException(status_code=500, detail="Game state not initialized")

    if state.synth < SYNTH_REQUIRED:
        raise HTTPException(
            status_code=400,
            detail=f"need {SYNTH_REQUIRED} Synth to prestige — you have {state.synth}"
        )

    # Carry-over values
    new_multiplier = round(state.cycle_multiplier * 1.5, 4)
    new_prestige_count = state.prestige_count + 1

    # Reset game state
    state.cycles = 0.0
    state.entropy = 0.0
    state.tier = 0
    state.synth = 0
    state.cycle_multiplier = new_multiplier
    state.prestige_count = new_prestige_count
    state.dark_ops_unlocked = True
    state.hmac_shards = 0

    # Reset all mission tracking counters
    state.mines_total = 0
    state.status_calls = 0
    state.patience_first_mine_at = None
    state.patience_first_entropy = None
    state.compressor_saw_high = False
    state.danger_mines = 0
    state.scheduler_mines = 0
    state.scheduler_active = False
    state.scheduler_last_mine_at = None
    state.scheduler_bad = False
    state.overclock_active = False
    state.overclock_mines = 0
    state.overclock_ends_at = None
    state.passive_ticks = 0
    # Reset blob companion
    state.blob_requests_total = 0
    state.blob_endpoints_seen = "[]"
    state.blob_dna_seed = -1
    state.blob_call_sequence = "[]"
    state.updated_at = datetime.utcnow()

    # Reset all missions
    missions = session.exec(select(Mission)).all()
    for m in missions:
        m.completed = False
        m.completed_at = None
        session.add(m)

    # Deactivate all automations
    automations = session.exec(select(Automation)).all()
    for a in automations:
        a.active = False
        session.add(a)

    result = {
        "message": "RESET PROTOCOL INITIATED — run complete",
        "prestige_count": new_prestige_count,
        "cycle_multiplier": new_multiplier,
        "dark_ops_unlocked": True,
        "note": "All cycles and missions reset. Multiplier and dark ops carry over.",
    }

    update_blob(state, "/prestige")
    session.add(CallLog(
        endpoint="/prestige", method="POST", status_code=200,
        result_json=json.dumps(result), timestamp=datetime.utcnow()
    ))
    session.add(state)
    session.commit()
    return result


@router.get("/prestige/status")
def get_prestige_status(session: Session = Depends(get_session)):
    state = session.exec(select(GameState)).first()
    if state is None:
        raise HTTPException(status_code=500, detail="Game state not initialized")
    return {
        "synth": state.synth,
        "synth_required": SYNTH_REQUIRED,
        "prestige_count": state.prestige_count,
        "cycle_multiplier": state.cycle_multiplier,
        "dark_ops_unlocked": state.dark_ops_unlocked,
        "ready": state.synth >= SYNTH_REQUIRED,
    }

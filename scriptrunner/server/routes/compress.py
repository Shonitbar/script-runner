"""POST /compress — spend 100 cycles to reduce entropy by 20."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from scriptrunner.server.db import get_session
from scriptrunner.server.models import CallLog, GameState
from scriptrunner.server.mission_engine import check_missions

router = APIRouter()

COMPRESS_COST = 100.0
COMPRESS_REDUCTION = 20.0


@router.post("/compress")
def post_compress(session: Session = Depends(get_session)):
    state = session.exec(select(GameState)).first()
    if state is None:
        raise HTTPException(status_code=500, detail="Game state not initialized")

    if state.tier < 2:
        raise HTTPException(status_code=403, detail="endpoint locked — reach Tier 2 first")

    if state.cycles < COMPRESS_COST:
        raise HTTPException(
            status_code=400,
            detail=f"insufficient cycles — need {COMPRESS_COST}, have {round(state.cycles, 2)}"
        )

    state.cycles -= COMPRESS_COST
    state.entropy = max(0.0, state.entropy - COMPRESS_REDUCTION)
    state.updated_at = datetime.utcnow()

    newly_completed = check_missions(state, session)

    result = {
        "cycles": round(state.cycles, 2),
        "entropy": round(state.entropy, 2),
        "message": f"compressed — entropy reduced by {COMPRESS_REDUCTION}",
    }
    if newly_completed:
        result["missions_completed"] = newly_completed

    session.add(CallLog(
        endpoint="/compress", method="POST", status_code=200,
        result_json=json.dumps(result), timestamp=datetime.utcnow()
    ))
    session.add(state)
    session.commit()
    return result

"""POST /automate — register a named automation for passive +0.5 cycles/sec."""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from scriptrunner.server.db import get_session
from scriptrunner.server.models import Automation, CallLog, GameState

router = APIRouter()


class AutomateRequest(BaseModel):
    name: str
    interval_sec: Optional[int] = 10


@router.post("/automate")
def post_automate(body: AutomateRequest, session: Session = Depends(get_session)):
    state = session.exec(select(GameState)).first()
    if state is None:
        raise HTTPException(status_code=500, detail="Game state not initialized")

    if state.tier < 2:
        raise HTTPException(status_code=403, detail="endpoint locked — reach Tier 2 first")

    if not body.name or len(body.name) > 64:
        raise HTTPException(status_code=400, detail="name must be 1–64 characters")

    existing = session.exec(
        select(Automation).where(Automation.name == body.name)
    ).first()

    if existing:
        existing.active = True
        existing.interval_sec = body.interval_sec
        existing.registered_at = datetime.utcnow()
        session.add(existing)
        msg = f"automation '{body.name}' reactivated"
    else:
        session.add(Automation(name=body.name, interval_sec=body.interval_sec))
        msg = f"automation '{body.name}' registered"

    result = {
        "name": body.name,
        "interval_sec": body.interval_sec,
        "passive_rate": "+0.5 cycles/sec",
        "message": msg,
    }
    session.add(CallLog(
        endpoint="/automate", method="POST", status_code=200,
        result_json=json.dumps(result), timestamp=datetime.utcnow()
    ))
    session.commit()
    return result


@router.get("/automate")
def get_automations(session: Session = Depends(get_session)):
    state = session.exec(select(GameState)).first()
    if state and state.tier < 2:
        raise HTTPException(status_code=403, detail="endpoint locked — reach Tier 2 first")

    automations = session.exec(select(Automation)).all()
    return [
        {
            "name": a.name,
            "interval_sec": a.interval_sec,
            "active": a.active,
            "registered_at": a.registered_at.isoformat(),
        }
        for a in automations
    ]

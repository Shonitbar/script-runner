"""GET /missions — list missions. Mission completion is auto-triggered by game actions."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from scriptrunner.server.db import get_session
from scriptrunner.server.models import Mission

router = APIRouter()


@router.get("/missions")
def get_missions(session: Session = Depends(get_session)):
    missions = session.exec(select(Mission).order_by(Mission.order)).all()
    return [
        {
            "id": m.id,
            "slug": m.slug,
            "name": m.name,
            "description": m.description,
            "tier_required": m.tier_required,
            "reward_cycles": m.reward_cycles,
            "reward_synth": m.reward_synth,
            "completed": m.completed,
            "completed_at": m.completed_at.isoformat() if m.completed_at else None,
        }
        for m in missions
    ]

"""GET /status/history — last 20 API calls. Unlocked after First Contact."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from scriptrunner.server.db import get_session
from scriptrunner.server.models import CallLog, Mission

router = APIRouter()


@router.get("/status/history")
def get_history(session: Session = Depends(get_session)):
    first_contact = session.exec(
        select(Mission).where(Mission.slug == "first_contact")
    ).first()
    if not first_contact or not first_contact.completed:
        raise HTTPException(status_code=403, detail="endpoint locked — complete First Contact first")

    logs = session.exec(
        select(CallLog).order_by(CallLog.timestamp.desc()).limit(20)
    ).all()
    return [
        {
            "endpoint": log.endpoint,
            "method": log.method,
            "status_code": log.status_code,
            "result": log.result_json,
            "timestamp": log.timestamp.isoformat(),
        }
        for log in logs
    ]

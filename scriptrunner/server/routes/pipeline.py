"""POST /pipeline — chain multiple operations in one request body."""

import json
import random
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from scriptrunner.server.db import get_session
from scriptrunner.server.models import CallLog, GameState, Mission
from scriptrunner.server.mission_engine import check_missions
from scriptrunner.server.state import update_blob

router = APIRouter()

ALLOWED_OPS = {"mine", "compress", "status"}


class PipelineOp(BaseModel):
    op: str


class PipelineRequest(BaseModel):
    ops: List[PipelineOp]


@router.post("/pipeline")
def post_pipeline(body: PipelineRequest, session: Session = Depends(get_session)):
    state = session.exec(select(GameState)).first()
    if state is None:
        raise HTTPException(status_code=500, detail="Game state not initialized")

    if state.tier < 3:
        raise HTTPException(status_code=403, detail="endpoint locked — reach Tier 3 first")

    if not body.ops:
        raise HTTPException(status_code=400, detail="ops list is empty")

    if len(body.ops) > 20:
        raise HTTPException(status_code=400, detail="max 20 ops per pipeline")

    results = []
    mine_count = 0
    compress_count = 0
    all_completed: List[str] = []

    for item in body.ops:
        op = item.op
        if op not in ALLOWED_OPS:
            results.append({"op": op, "error": f"unknown op '{op}'"})
            continue

        if op == "mine":
            entropy = state.entropy
            if entropy >= 90:
                results.append({"op": "mine", "error": "entropy critical"})
                continue
            if entropy < 30:
                gain = 1
            elif entropy < 70:
                gain = 2
            else:
                gain = 5
            gain *= state.cycle_multiplier
            loss = entropy >= 70 and random.random() < 0.10
            if loss:
                state.cycles = max(0, state.cycles - 50)
                results.append({"op": "mine", "gained": 0, "lost": 50, "zone": "danger"})
            else:
                state.cycles += gain
                results.append({"op": "mine", "gained": round(gain, 2),
                                 "zone": "safe" if entropy < 30 else "caution" if entropy < 70 else "danger"})
            state.entropy = min(100, state.entropy + 0.5)
            state.mines_total += 1
            if entropy > 70:
                state.danger_mines += 1
            mine_count += 1

        elif op == "compress":
            if state.cycles < 100:
                results.append({"op": "compress", "error": "insufficient cycles"})
                continue
            state.cycles -= 100
            state.entropy = max(0, state.entropy - 20)
            results.append({"op": "compress", "entropy": round(state.entropy, 2)})
            compress_count += 1

        elif op == "status":
            results.append({
                "op": "status",
                "cycles": round(state.cycles, 2),
                "entropy": round(state.entropy, 2),
                "tier": state.tier,
            })
            state.status_calls += 1

    state.updated_at = datetime.utcnow()
    newly_completed = check_missions(state, session)
    all_completed.extend(newly_completed)

    # Pipeline Engineer mission: mine>=3, compress>=1, mine>=3 (in that order, total 6 mines + 1 compress)
    ops_seq = [o.op for o in body.ops]
    if mine_count >= 6 and compress_count >= 1:
        pe = session.exec(
            select(Mission).where(Mission.slug == "pipeline_engineer")
        ).first()
        if pe and not pe.completed:
            pe.completed = True
            pe.completed_at = datetime.utcnow()
            state.cycles += pe.reward_cycles * state.cycle_multiplier
            state.synth += pe.reward_synth
            session.add(pe)
            all_completed.append("pipeline_engineer")

    result_payload = {
        "results": results,
        "cycles": round(state.cycles, 2),
        "entropy": round(state.entropy, 2),
    }
    if all_completed:
        result_payload["missions_completed"] = all_completed

    update_blob(state, "/pipeline")
    session.add(CallLog(
        endpoint="/pipeline", method="POST", status_code=200,
        result_json=json.dumps(result_payload), timestamp=datetime.utcnow()
    ))
    session.add(state)
    session.commit()
    return result_payload

"""Dark Ops endpoints — prestige-only. HMAC puzzle + high-risk operations."""

import hashlib
import hmac
import json
import random
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from scriptrunner.server.db import get_session
from scriptrunner.server.models import CallLog, GameState
from scriptrunner.server.state import update_blob

router = APIRouter(prefix="/dark-ops")

# The HMAC key — split into 5 shards across the hint endpoints.
# Players must collect all fragments and concatenate in order (1-5).
_KEY_SHARDS = [
    "sc",   # shard 1: GET /dark-ops/hint/1
    "ri",   # shard 2: GET /dark-ops/hint/2
    "pt",   # shard 3: GET /dark-ops/hint/3
    "ru",   # shard 4: GET /dark-ops/hint/4
    "n!",   # shard 5: GET /dark-ops/hint/5
]
# Full key: "scriptrun!" — players reconstruct by collecting shards 1-5
HMAC_KEY = "".join(_KEY_SHARDS).encode()

# Manifest clues — cryptic references pointing to the 5 hint endpoints
_MANIFEST = """
> DARK OPS MANIFEST — CLASSIFIED
> Access level: PRESTIGE+

Fragment dispersal protocol active.
Five shards. Five endpoints. One key.

  [SYS_LOG_0x01] /dark-ops/hint/1  — "where cycles begin, so does the truth"
  [SYS_LOG_0x02] /dark-ops/hint/2  — "the second breath of the machine"
  [SYS_LOG_0x03] /dark-ops/hint/3  — "halfway through the word that names this world"
  [SYS_LOG_0x04] /dark-ops/hint/4  — "two letters before the end"
  [SYS_LOG_0x05] /dark-ops/hint/5  — "the final punctuation of the protocol"

When all five are yours, concatenate in order.
Sign the payload with HMAC-SHA256.
Submit to POST /dark-ops/finalize.

Payload format: {"timestamp": <unix_epoch_int>, "agent": "<your_name>"}
Signature header: X-Signature: <hex_digest>

> END MANIFEST
"""


def _require_dark_ops(state: GameState) -> None:
    if not state.dark_ops_unlocked:
        raise HTTPException(
            status_code=403,
            detail="dark ops locked — complete prestige (5 Synth) to unlock"
        )


def _get_state(session: Session) -> GameState:
    state = session.exec(select(GameState)).first()
    if state is None:
        raise HTTPException(status_code=500, detail="Game state not initialized")
    return state


@router.get("/manifest")
def get_manifest(session: Session = Depends(get_session)):
    state = _get_state(session)
    _require_dark_ops(state)
    return {"manifest": _MANIFEST}


@router.get("/hint/{shard_id}")
def get_hint(shard_id: int, session: Session = Depends(get_session)):
    state = _get_state(session)
    _require_dark_ops(state)

    if shard_id < 1 or shard_id > 5:
        raise HTTPException(status_code=404, detail="shard not found")

    # Track which shards the player has collected via bitmask
    bit = 1 << (shard_id - 1)
    if not (state.hmac_shards & bit):
        state.hmac_shards |= bit
        state.updated_at = datetime.utcnow()
        session.add(state)
        session.commit()

    shard = _KEY_SHARDS[shard_id - 1]
    collected = bin(state.hmac_shards).count("1")
    return {
        "shard_id": shard_id,
        "fragment": shard,
        "shards_collected": collected,
        "shards_total": 5,
        "hint": f"fragment {shard_id} of 5 acquired",
    }


class SpoofRequest(BaseModel):
    payload: dict
    signature: str  # hex HMAC-SHA256 of JSON-serialized payload


@router.post("/spoof")
def post_spoof(body: SpoofRequest, session: Session = Depends(get_session)):
    state = _get_state(session)
    _require_dark_ops(state)

    payload_bytes = json.dumps(body.payload, separators=(",", ":"), sort_keys=True).encode()
    expected = hmac.new(HMAC_KEY, payload_bytes, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, body.signature.lower()):
        # Penalty: entropy spike
        state.entropy = min(100, state.entropy + 20)
        state.updated_at = datetime.utcnow()
        session.add(state)
        session.commit()
        raise HTTPException(
            status_code=401,
            detail="invalid signature — entropy +20"
        )

    gain = 200.0 * state.cycle_multiplier
    state.cycles += gain
    state.updated_at = datetime.utcnow()

    result = {
        "outcome": "spoof accepted",
        "gained": round(gain, 2),
        "cycles": round(state.cycles, 2),
        "message": "the machine believed you",
    }
    update_blob(state, "/dark-ops/spoof")
    session.add(CallLog(
        endpoint="/dark-ops/spoof", method="POST", status_code=200,
        result_json=json.dumps(result), timestamp=datetime.utcnow()
    ))
    session.add(state)
    session.commit()
    return result


@router.post("/inject")
def post_inject(session: Session = Depends(get_session)):
    """Inject a fake automation event. Extremely high risk."""
    state = _get_state(session)
    _require_dark_ops(state)

    roll = random.random()
    if roll < 0.33:
        # Critical failure
        state.entropy = min(100, state.entropy + 50)
        state.cycles = max(0, state.cycles - 200)
        state.updated_at = datetime.utcnow()
        result = {
            "outcome": "critical_failure",
            "entropy": round(state.entropy, 2),
            "message": "injection detected — entropy +50, lost 200 cycles",
        }
    elif roll < 0.66:
        # Partial success
        gain = 100.0 * state.cycle_multiplier
        state.cycles += gain
        state.entropy = min(100, state.entropy + 15)
        state.updated_at = datetime.utcnow()
        result = {
            "outcome": "partial_success",
            "gained": round(gain, 2),
            "entropy": round(state.entropy, 2),
            "message": "injection partially accepted",
        }
    else:
        # Full success
        gain = 400.0 * state.cycle_multiplier
        state.cycles += gain
        state.updated_at = datetime.utcnow()
        result = {
            "outcome": "success",
            "gained": round(gain, 2),
            "cycles": round(state.cycles, 2),
            "message": "injection accepted — ghost automation registered",
        }

    update_blob(state, "/dark-ops/inject")
    session.add(CallLog(
        endpoint="/dark-ops/inject", method="POST", status_code=200,
        result_json=json.dumps(result), timestamp=datetime.utcnow()
    ))
    session.add(state)
    session.commit()
    return result


class FinalizeRequest(BaseModel):
    timestamp: int
    agent: str
    signature: str  # hex HMAC-SHA256 of {"timestamp":<int>,"agent":"<str>"}


@router.post("/finalize")
def post_finalize(body: FinalizeRequest, session: Session = Depends(get_session)):
    """The secret final mission. Must have all 5 shards and correct HMAC signature."""
    state = _get_state(session)
    _require_dark_ops(state)

    if state.hmac_shards != 0b11111:
        raise HTTPException(
            status_code=403,
            detail=f"incomplete — collect all 5 shards first ({bin(state.hmac_shards).count('1')}/5 collected)"
        )

    # Timestamp must be within 5 minutes to prevent replay
    now = int(time.time())
    if abs(now - body.timestamp) > 300:
        raise HTTPException(status_code=400, detail="timestamp expired — must be within 5 minutes")

    payload_bytes = json.dumps(
        {"timestamp": body.timestamp, "agent": body.agent},
        separators=(",", ":"), sort_keys=True
    ).encode()
    expected = hmac.new(HMAC_KEY, payload_bytes, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, body.signature.lower()):
        state.entropy = min(100, state.entropy + 30)
        state.updated_at = datetime.utcnow()
        session.add(state)
        session.commit()
        raise HTTPException(status_code=401, detail="invalid signature — entropy +30")

    # Grant the ultimate reward
    gain = 99999.0 * state.cycle_multiplier
    state.cycles += gain
    state.synth += 10
    state.updated_at = datetime.utcnow()

    result = {
        "outcome": "CLASSIFIED",
        "message": f"PROTOCOL COMPLETE — well played, {body.agent}",
        "gained": round(gain, 2),
        "synth_gained": 10,
        "cycles": round(state.cycles, 2),
        "secret": "the key was the name of the game all along",
    }

    update_blob(state, "/dark-ops/finalize")
    session.add(CallLog(
        endpoint="/dark-ops/finalize", method="POST", status_code=200,
        result_json=json.dumps(result), timestamp=datetime.utcnow()
    ))
    session.add(state)
    session.commit()
    return result

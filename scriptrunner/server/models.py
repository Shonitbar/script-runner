from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class GameState(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cycles: float = Field(default=0.0)
    entropy: float = Field(default=0.0)
    synth: int = Field(default=0)
    tier: int = Field(default=0)
    cycle_multiplier: float = Field(default=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CallLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint: str
    method: str = Field(default="POST")
    status_code: int
    result_json: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

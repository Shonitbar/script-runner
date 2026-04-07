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
    # Mission tracking counters
    mines_total: int = Field(default=0)
    status_calls: int = Field(default=0)
    # Patience mission: timestamp of the "first mine" trigger
    patience_first_mine_at: Optional[datetime] = Field(default=None)
    patience_first_entropy: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CallLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint: str
    method: str = Field(default="POST")
    status_code: int
    result_json: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Mission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    name: str
    description: str
    tier_required: int = Field(default=0)
    reward_cycles: float = Field(default=0.0)
    reward_synth: int = Field(default=0)
    # completion_type: mine_once | mine_n | status_n | patience | accumulate_cycles
    completion_type: str
    completion_value: int = Field(default=1)
    completed: bool = Field(default=False)
    completed_at: Optional[datetime] = Field(default=None)
    order: int = Field(default=0)

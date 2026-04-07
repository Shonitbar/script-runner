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
    # Patience mission tracking
    patience_first_mine_at: Optional[datetime] = Field(default=None)
    patience_first_entropy: Optional[float] = Field(default=None)
    # Compressor mission tracking (saw entropy >70 flag)
    compressor_saw_high: bool = Field(default=False)
    # Danger zone mission tracking
    danger_mines: int = Field(default=0)
    # Scheduler mission tracking
    scheduler_mines: int = Field(default=0)
    scheduler_active: bool = Field(default=False)
    scheduler_last_mine_at: Optional[datetime] = Field(default=None)
    scheduler_bad: bool = Field(default=False)
    # Overclock mission tracking
    overclock_active: bool = Field(default=False)
    overclock_mines: int = Field(default=0)
    overclock_ends_at: Optional[datetime] = Field(default=None)
    # Passive income tick counter (for Full Auto mission)
    passive_ticks: int = Field(default=0)
    # Prestige
    prestige_count: int = Field(default=0)
    dark_ops_unlocked: bool = Field(default=False)
    # Dark ops: HMAC key shards collected (bitmask 0b11111 = all 5)
    hmac_shards: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CallLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    endpoint: str
    method: str = Field(default="POST")
    status_code: int
    result_json: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Automation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    interval_sec: int = Field(default=10)
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = Field(default=True)


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

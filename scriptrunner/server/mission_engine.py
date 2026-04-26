"""Auto-checks and completes missions based on current game state."""

from datetime import datetime, timezone
from typing import List

from sqlmodel import Session, select

from scriptrunner.server.models import GameState, Mission

# Tier thresholds
TIER_CYCLE_GOALS = {1: 0, 2: 500, 3: 5000, 4: 50000}


def _complete(mission: Mission, state: GameState, session: Session, completed: List[str]) -> None:
    if mission.completed:
        return
    mission.completed = True
    mission.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    state.cycles += mission.reward_cycles * state.cycle_multiplier
    state.synth += mission.reward_synth
    state.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(mission)
    completed.append(mission.slug)


def _promote_tier(state: GameState, target: int) -> None:
    if state.tier < target:
        state.tier = target
        state.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)


def check_missions(state: GameState, session: Session) -> List[str]:
    """Run after any game action. Returns list of newly completed mission slugs."""
    missions = {
        m.slug: m
        for m in session.exec(
            select(Mission).where(Mission.completed == False)  # noqa: E712
        ).all()
    }
    completed: List[str] = []

    # ── Tier 0 ────────────────────────────────────────────────────────────
    if "first_contact" in missions and state.mines_total >= 1:
        _complete(missions["first_contact"], state, session, completed)
        _promote_tier(state, 1)

    # ── Tier 1 ────────────────────────────────────────────────────────────
    if state.tier >= 1:
        if "ten_in_a_row" in missions and state.mines_total >= 10:
            _complete(missions["ten_in_a_row"], state, session, completed)

        if "the_watcher" in missions and state.status_calls >= 20:
            _complete(missions["the_watcher"], state, session, completed)

        if "patience" in missions:
            m = missions["patience"]
            if state.patience_first_mine_at is None and state.mines_total >= 1:
                state.patience_first_mine_at = datetime.now(timezone.utc).replace(tzinfo=None)
                state.patience_first_entropy = state.entropy
                state.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            elif (
                state.patience_first_mine_at is not None
                and state.entropy < 2.0
                and state.mines_total >= 2
            ):
                _complete(m, state, session, completed)

        if "grinder" in missions and state.cycles >= 500:
            _complete(missions["grinder"], state, session, completed)
            _promote_tier(state, 2)

    # ── Tier 2 ────────────────────────────────────────────────────────────
    if state.tier >= 2:
        if "loop_artist" in missions and state.mines_total >= 50:
            _complete(missions["loop_artist"], state, session, completed)

        if "the_compressor" in missions:
            m = missions["the_compressor"]
            if state.entropy > 70:
                state.compressor_saw_high = True
                state.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            if state.compressor_saw_high and state.entropy < 30:
                _complete(m, state, session, completed)

        if "danger_zone" in missions and state.danger_mines >= 5:
            _complete(missions["danger_zone"], state, session, completed)

        if "the_scheduler" in missions and state.scheduler_mines >= 30 and not state.scheduler_bad:
            _complete(missions["the_scheduler"], state, session, completed)

        if "scaler" in missions and state.cycles >= 5000:
            _complete(missions["scaler"], state, session, completed)
            _promote_tier(state, 3)

    # ── Tier 3 ────────────────────────────────────────────────────────────
    if state.tier >= 3:
        if "pipeline_engineer" in missions:
            pass  # completed inline by /pipeline route

        if "overclock_runner" in missions and state.overclock_mines >= 25:
            _complete(missions["overclock_runner"], state, session, completed)

        if "full_auto" in missions and state.passive_ticks >= 600:
            _complete(missions["full_auto"], state, session, completed)

        if "titan" in missions and state.cycles >= 50000:
            _complete(missions["titan"], state, session, completed)

    session.add(state)
    return completed

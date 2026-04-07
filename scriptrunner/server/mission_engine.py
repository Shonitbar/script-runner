"""Auto-checks and completes missions based on current game state."""

from datetime import datetime
from typing import List

from sqlmodel import Session, select

from scriptrunner.server.models import GameState, Mission


def _complete(mission: Mission, state: GameState, session: Session, completed: List[str]) -> None:
    if mission.completed:
        return
    mission.completed = True
    mission.completed_at = datetime.utcnow()
    state.cycles += mission.reward_cycles
    state.synth += mission.reward_synth
    state.updated_at = datetime.utcnow()
    session.add(mission)
    completed.append(mission.slug)


def check_missions(state: GameState, session: Session) -> List[str]:
    """Run after any game action. Returns list of newly completed mission slugs."""
    missions = {
        m.slug: m
        for m in session.exec(
            select(Mission).where(Mission.completed == False)  # noqa: E712
        ).all()
    }
    completed: List[str] = []

    # --- Tier 0 ---
    if "first_contact" in missions and state.mines_total >= 1:
        _complete(missions["first_contact"], state, session, completed)
        # Tier promotion: 0 → 1
        if state.tier == 0:
            state.tier = 1
            state.updated_at = datetime.utcnow()

    # --- Tier 1 (only available once tier >= 1) ---
    if state.tier >= 1:
        if "ten_in_a_row" in missions and state.mines_total >= 10:
            _complete(missions["ten_in_a_row"], state, session, completed)

        if "the_watcher" in missions and state.status_calls >= 20:
            _complete(missions["the_watcher"], state, session, completed)

        if "patience" in missions:
            m = missions["patience"]
            # Phase 1: player has mined at least once — record the trigger point
            if state.patience_first_mine_at is None and state.mines_total >= 1:
                state.patience_first_mine_at = datetime.utcnow()
                state.patience_first_entropy = state.entropy
                state.updated_at = datetime.utcnow()
            # Phase 2: entropy below 2.0 AND a second mine happened after trigger
            elif (
                state.patience_first_mine_at is not None
                and state.entropy < 2.0
                and state.mines_total >= 2
            ):
                _complete(m, state, session, completed)

        if "grinder" in missions and state.cycles >= 500:
            _complete(missions["grinder"], state, session, completed)
            # Tier promotion: 1 → 2
            if state.tier == 1:
                state.tier = 2
                state.updated_at = datetime.utcnow()

    session.add(state)
    return completed

from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, select

_data_dir = Path.home() / ".scriptrunner"
_data_dir.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{_data_dir / 'save.db'}"

engine = create_engine(DATABASE_URL, echo=False)

_MISSIONS = [
    # Tier 0
    dict(slug="first_contact", name="First Contact", tier_required=0, order=0,
         description="Call POST /mine once.",
         completion_type="mine_once", completion_value=1,
         reward_cycles=10.0, reward_synth=0),
    # Tier 1
    dict(slug="ten_in_a_row", name="Ten in a Row", tier_required=1, order=1,
         description="Mine 10 times.",
         completion_type="mine_n", completion_value=10,
         reward_cycles=50.0, reward_synth=0),
    dict(slug="the_watcher", name="The Watcher", tier_required=1, order=2,
         description="Call GET /status 20 times.",
         completion_type="status_n", completion_value=20,
         reward_cycles=80.0, reward_synth=0),
    dict(slug="patience", name="Patience", tier_required=1, order=3,
         description="Mine once, wait until entropy < 2.0, then mine again.",
         completion_type="patience", completion_value=1,
         reward_cycles=120.0, reward_synth=0),
    dict(slug="grinder", name="Grinder", tier_required=1, order=4,
         description="Accumulate 500 cycles total.",
         completion_type="accumulate_cycles", completion_value=500,
         reward_cycles=0.0, reward_synth=1),
]


def init_db() -> None:
    SQLModel.metadata.create_all(engine)

    from scriptrunner.server.models import GameState, Mission
    with Session(engine) as session:
        if session.exec(select(GameState)).first() is None:
            session.add(GameState())

        for m in _MISSIONS:
            if session.exec(select(Mission).where(Mission.slug == m["slug"])).first() is None:
                session.add(Mission(**m))

        session.commit()


def get_session():
    with Session(engine) as session:
        yield session

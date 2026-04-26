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
         description="Mine 10 times total.",
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
    # Tier 2
    dict(slug="loop_artist", name="Loop Artist", tier_required=2, order=5,
         description="Mine 50 times total.",
         completion_type="mine_n", completion_value=50,
         reward_cycles=300.0, reward_synth=1),
    dict(slug="the_compressor", name="The Compressor", tier_required=2, order=6,
         description="Let entropy reach > 70, then compress it back below 30.",
         completion_type="compressor", completion_value=1,
         reward_cycles=200.0, reward_synth=0),
    dict(slug="danger_zone", name="Danger Zone", tier_required=2, order=7,
         description="Mine 5 times while entropy > 70.",
         completion_type="danger_mines", completion_value=5,
         reward_cycles=0.0, reward_synth=1),
    dict(slug="the_scheduler", name="The Scheduler", tier_required=2, order=8,
         description="Mine exactly once every 2 seconds for 60 seconds (±200ms tolerance).",
         completion_type="scheduler", completion_value=30,
         reward_cycles=400.0, reward_synth=0),
    dict(slug="scaler", name="Scaler", tier_required=2, order=9,
         description="Accumulate 5,000 cycles total.",
         completion_type="accumulate_cycles", completion_value=5000,
         reward_cycles=0.0, reward_synth=1),
    # Tier 3
    dict(slug="pipeline_engineer", name="Pipeline Engineer", tier_required=3, order=10,
         description="Submit a /pipeline request that mines 3 times, compresses once, mines 3 more.",
         completion_type="pipeline_run", completion_value=1,
         reward_cycles=2000.0, reward_synth=0),
    dict(slug="overclock_runner", name="Overclock Runner", tier_required=3, order=11,
         description="Overclock then mine more than 25 times in the 30-second window.",
         completion_type="overclock_mines", completion_value=25,
         reward_cycles=3000.0, reward_synth=0),
    dict(slug="full_auto", name="Full Auto", tier_required=3, order=12,
         description="Run an automation for 10 minutes unattended (600 passive ticks).",
         completion_type="passive_ticks", completion_value=600,
         reward_cycles=5000.0, reward_synth=2),
    dict(slug="titan", name="Titan", tier_required=3, order=13,
         description="Accumulate 50,000 cycles total.",
         completion_type="accumulate_cycles", completion_value=50000,
         reward_cycles=0.0, reward_synth=5),
]


def _migrate_blob_columns() -> None:
    """Add blob companion columns to existing databases that predate this feature."""
    from sqlalchemy import text
    migrations = [
        ("blob_requests_total", "INTEGER DEFAULT 0"),
        ("blob_endpoints_seen", "TEXT DEFAULT '[]'"),
        ("blob_dna_seed", "INTEGER DEFAULT -1"),
        ("blob_call_sequence", "TEXT DEFAULT '[]'"),
    ]
    with engine.connect() as conn:
        for col_name, col_def in migrations:
            try:
                conn.execute(text(f"ALTER TABLE gamestate ADD COLUMN {col_name} {col_def}"))
                conn.commit()
            except Exception:
                pass  # Column already exists


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _migrate_blob_columns()

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

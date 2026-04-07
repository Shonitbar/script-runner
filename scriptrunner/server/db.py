from sqlmodel import SQLModel, create_engine, Session, select

DATABASE_URL = "sqlite:///scriptrunner.db"

engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    # Seed initial game state row if not present
    from scriptrunner.server.models import GameState
    with Session(engine) as session:
        existing = session.exec(select(GameState)).first()
        if existing is None:
            session.add(GameState())
            session.commit()


def get_session():
    with Session(engine) as session:
        yield session

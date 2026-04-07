from contextlib import asynccontextmanager

from fastapi import FastAPI

from scriptrunner.server.db import init_db
from scriptrunner.server.state import start_decay_loop


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await start_decay_loop()
    yield


app = FastAPI(title="ScriptRunner", lifespan=lifespan)

# Routes registered here as features are added
from scriptrunner.server.routes import (  # noqa: E402
    core, ws, missions, history, compress, automate, pipeline
)
app.include_router(core.router)
app.include_router(ws.router)
app.include_router(missions.router)
app.include_router(history.router)
app.include_router(compress.router)
app.include_router(automate.router)
app.include_router(pipeline.router)

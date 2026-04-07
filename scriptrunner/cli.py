import multiprocessing
import subprocess
import sys
import time

import typer

app = typer.Typer(help="ScriptRunner — a terminal-native idle game.")


def _run_server() -> None:
    import uvicorn
    uvicorn.run(
        "scriptrunner.server.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="warning",
    )


def _run_tui() -> None:
    from scriptrunner.tui.app import ScriptRunnerApp
    ScriptRunnerApp().run()


@app.command()
def start() -> None:
    """Start the ScriptRunner server and TUI dashboard."""
    typer.echo("  SCRIPTRUNNER  booting...\n")

    server_proc = multiprocessing.Process(target=_run_server, daemon=True)
    server_proc.start()

    # Give server a moment to bind
    time.sleep(1.0)

    try:
        _run_tui()
    finally:
        server_proc.terminate()
        server_proc.join(timeout=3)


@app.command()
def server() -> None:
    """Start only the game server (no TUI)."""
    import uvicorn
    typer.echo("Starting ScriptRunner server on http://localhost:8000")
    uvicorn.run(
        "scriptrunner.server.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )

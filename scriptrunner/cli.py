import multiprocessing
import os
import signal
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


def _shutdown(proc: multiprocessing.Process) -> None:
    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=3)
    if proc.is_alive():
        proc.kill()
        proc.join(timeout=2)


@app.command()
def start() -> None:
    """Start the ScriptRunner server and TUI dashboard."""
    typer.echo("  SCRIPTRUNNER  booting...\n")

    server_proc = multiprocessing.Process(target=_run_server, daemon=True)
    server_proc.start()

    # Forward SIGTERM/SIGINT to the server process, then exit cleanly
    def _handle_signal(signum, frame):
        _shutdown(server_proc)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    # Give server a moment to bind
    time.sleep(1.0)

    try:
        from scriptrunner.tui.app import ScriptRunnerApp
        ScriptRunnerApp().run()
    finally:
        _shutdown(server_proc)


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

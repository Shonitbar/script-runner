"""ScriptRunner TUI — Feature 5: CORE panel with live WebSocket updates."""

import json

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from scriptrunner.tui.widgets.core_panel import CorePanel

WS_URL = "ws://127.0.0.1:8000/ws"


class ScriptRunnerApp(App):
    TITLE = "SCRIPTRUNNER"
    CSS = """
    Screen {
        background: #0a0a0a;
        align: center top;
        padding: 1;
    }
    CorePanel {
        width: 46;
        height: auto;
        margin: 0;
    }
    """
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield CorePanel()
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._connect_ws, exclusive=True)

    async def _connect_ws(self) -> None:
        import asyncio
        import websockets

        panel = self.query_one(CorePanel)
        while True:
            try:
                async with websockets.connect(WS_URL) as ws:
                    async for message in ws:
                        data = json.loads(message)
                        if data.get("type") == "state":
                            panel.cycles = data["cycles"]
                            panel.entropy = data["entropy"]
                            panel.synth = data["synth"]
                            panel.tier = data["tier"]
                            panel.uptime = data["uptime"]
                            panel.cycle_multiplier = data["cycle_multiplier"]
            except Exception:
                # Server not ready or disconnected — retry after 2s
                await asyncio.sleep(2)

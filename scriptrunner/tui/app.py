"""ScriptRunner TUI — full dashboard with CORE, MISSIONS, and LOG panels."""

import asyncio
import json

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from scriptrunner.tui.widgets.core_panel import CorePanel
from scriptrunner.tui.widgets.missions_panel import MissionsPanel
from scriptrunner.tui.widgets.log_panel import LogPanel

WS_URL = "ws://127.0.0.1:8000/ws"


class ScriptRunnerApp(App):
    TITLE = "SCRIPTRUNNER"
    CSS = """
    Screen {
        background: #0a0a0a;
        layout: vertical;
        align: center top;
        padding: 1;
    }
    CorePanel {
        width: 46;
        height: auto;
        margin-bottom: 1;
    }
    MissionsPanel {
        width: 46;
        height: auto;
        margin-bottom: 1;
    }
    LogPanel {
        width: 46;
        height: auto;
    }
    """
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield CorePanel()
        yield MissionsPanel()
        yield LogPanel()
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._connect_ws, exclusive=True)

    async def _connect_ws(self) -> None:
        import websockets

        core = self.query_one(CorePanel)
        missions_panel = self.query_one(MissionsPanel)
        log_panel = self.query_one(LogPanel)

        while True:
            try:
                async with websockets.connect(WS_URL) as ws:
                    async for message in ws:
                        data = json.loads(message)
                        if data.get("type") == "state":
                            core.cycles = data["cycles"]
                            core.entropy = data["entropy"]
                            core.synth = data["synth"]
                            core.tier = data["tier"]
                            core.uptime = data["uptime"]
                            core.cycle_multiplier = data["cycle_multiplier"]
                            missions_panel.missions = data.get("missions", [])
                            log_panel.logs = data.get("logs", [])
            except Exception:
                await asyncio.sleep(2)

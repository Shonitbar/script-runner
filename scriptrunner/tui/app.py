"""ScriptRunner TUI — full dashboard."""

import asyncio
import json

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from scriptrunner.tui.widgets.automations_panel import AutomationsPanel
from scriptrunner.tui.widgets.blob_panel import BlobPanel
from scriptrunner.tui.widgets.core_panel import CorePanel
from scriptrunner.tui.widgets.entropy_gauge import EntropyGauge
from scriptrunner.tui.widgets.log_panel import LogPanel
from scriptrunner.tui.widgets.missions_panel import MissionsPanel

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
    CorePanel, MissionsPanel, LogPanel, AutomationsPanel, EntropyGauge, BlobPanel {
        width: 46;
        height: auto;
        margin-bottom: 1;
    }
    """
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield BlobPanel()
        yield CorePanel()
        yield EntropyGauge()
        yield MissionsPanel()
        yield AutomationsPanel()
        yield LogPanel()
        yield Footer()

    def on_mount(self) -> None:
        self.run_worker(self._connect_ws, exclusive=True)

    async def _connect_ws(self) -> None:
        import websockets

        blob_panel = self.query_one(BlobPanel)
        core = self.query_one(CorePanel)
        gauge = self.query_one(EntropyGauge)
        missions_panel = self.query_one(MissionsPanel)
        log_panel = self.query_one(LogPanel)
        automations_panel = self.query_one(AutomationsPanel)

        while True:
            try:
                async with websockets.connect(WS_URL) as ws:
                    async for message in ws:
                        data = json.loads(message)
                        t = data.get("type")

                        if t == "state":
                            blob = data.get("blob", {})
                            blob_panel.total_requests = blob.get("total_requests", 0)
                            blob_panel.endpoints_seen = blob.get("endpoints_seen", [])
                            blob_panel.dna_seed = blob.get("dna_seed", -1)
                            blob_panel.entropy = data["entropy"]
                            core.cycles = data["cycles"]
                            core.entropy = data["entropy"]
                            core.synth = data["synth"]
                            core.tier = data["tier"]
                            core.uptime = data["uptime"]
                            core.cycle_multiplier = data["cycle_multiplier"]
                            core.overclock_active = data.get("overclock_active", False)
                            core.overclock_remaining = data.get("overclock_remaining", 0)
                            core.prestige_count = data.get("prestige_count", 0)
                            core.dark_ops_unlocked = data.get("dark_ops_unlocked", False)
                            gauge.entropy = data["entropy"]
                            missions_panel.missions = data.get("missions", [])
                            log_panel.logs = data.get("logs", [])
                            automations_panel.automations = data.get("automations", [])
                            automations_panel.overclock_active = data.get("overclock_active", False)
                            automations_panel.overclock_remaining = data.get("overclock_remaining", 0)

                        elif t == "entropy_spike":
                            # Flash the core panel briefly to signal the spike
                            core.add_class("spike")
                            await asyncio.sleep(0.5)
                            core.remove_class("spike")
            except Exception:
                await asyncio.sleep(2)

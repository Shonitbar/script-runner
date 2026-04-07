import textwrap

from rich.text import Text
from textual.events import Click
from textual.reactive import reactive
from textual.widget import Widget


class MissionsPanel(Widget):
    missions: reactive[list] = reactive([], layout=True)
    expanded: reactive[frozenset] = reactive(frozenset(), layout=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._click_map: dict[int, str] = {}  # widget-relative line -> mission name

    def _toggle(self, name: str) -> None:
        if name in self.expanded:
            self.expanded = self.expanded - {name}
        else:
            self.expanded = self.expanded | {name}

    def on_click(self, event: Click) -> None:
        name = self._click_map.get(event.y)
        if name:
            self._toggle(name)

    def render(self) -> Text:
        self._click_map = {}
        out = Text()
        ln = 0  # current line index

        out.append("╔══════════════════════════════════════════╗\n", style="dim"); ln += 1
        out.append("║  MISSIONS                                ║\n", style="bold white"); ln += 1
        out.append("╠══════════════════════════════════════════╣\n", style="dim"); ln += 1

        pending = [m for m in self.missions if not m["completed"]]
        done    = [m for m in self.missions if m["completed"]]

        if not pending and not done:
            out.append("║  No missions available yet...            ║\n", style="dim"); ln += 1
        else:
            for m in pending:
                name = m["name"]
                is_open = name in self.expanded
                arrow = "▼" if is_open else "▶"

                reward = ""
                if m["reward_cycles"]:
                    reward += f"+{m['reward_cycles']:.0f}⚙"
                if m["reward_synth"]:
                    reward += f" +{m['reward_synth']}◈"

                # Name row — clicking here toggles the dropdown
                self._click_map[ln] = name
                row = f"║  {arrow} {name:<20}{reward:<8}"
                out.append(row.ljust(43), style="yellow")
                out.append("║\n", style="dim"); ln += 1

                if is_open:
                    # Wrap full description across as many lines as needed
                    for part in textwrap.wrap(m["description"], 38):
                        desc_row = f"║    {part}"
                        out.append(desc_row.ljust(43), style="dim")
                        out.append("║\n", style="dim"); ln += 1
                else:
                    # Single truncated preview line
                    preview = m["description"][:36]
                    if len(m["description"]) > 36:
                        preview = preview.rstrip() + "…"
                    desc_row = f"║    {preview}"
                    out.append(desc_row.ljust(43), style="dim")
                    out.append("║\n", style="dim"); ln += 1

            if done:
                out.append("╠══════════════════════════════════════════╣\n", style="dim"); ln += 1
                out.append("║  COMPLETED                               ║\n", style="dim green"); ln += 1
                for m in done[-3:]:
                    row = f"║  ✓ {m['name']}"
                    out.append(row.ljust(43), style="green")
                    out.append("║\n", style="dim"); ln += 1

        out.append("╚══════════════════════════════════════════╝", style="dim")
        return out

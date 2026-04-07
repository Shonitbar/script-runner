from rich.text import Text
from textual.widget import Widget
from textual.reactive import reactive


class AutomationsPanel(Widget):
    automations: reactive[list] = reactive([], layout=True)
    overclock_active: reactive[bool] = reactive(False)
    overclock_remaining: reactive[int] = reactive(0)

    def render(self) -> Text:
        out = Text()
        out.append("╔══════════════════════════════════════════╗\n", style="dim")
        out.append("║  AUTOMATIONS                             ║\n", style="bold white")
        out.append("╠══════════════════════════════════════════╣\n", style="dim")

        if self.overclock_active:
            line = f"║  ⚡ OVERCLOCK ACTIVE  {self.overclock_remaining:>2}s remaining"
            out.append(line.ljust(43), style="bold yellow")
            out.append("║\n", style="dim")

        if not self.automations:
            out.append("║  No automations registered               ║\n", style="dim")
            out.append("║  POST /automate to register one          ║\n", style="dim")
        else:
            for a in self.automations:
                line = f"║  ◉ {a['name']:<24} {a['interval_sec']}s interval"
                out.append(line.ljust(43), style="green")
                out.append("║\n", style="dim")
            passive = len(self.automations) * 0.5
            out.append(f"║  passive: +{passive:.1f} cycles/sec".ljust(43), style="dim green")
            out.append("║\n", style="dim")

        out.append("╚══════════════════════════════════════════╝", style="dim")
        return out

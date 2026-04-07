from rich.text import Text
from textual.widget import Widget
from textual.reactive import reactive


class LogPanel(Widget):
    logs: reactive[list] = reactive([], layout=True)

    def render(self) -> Text:
        out = Text()
        out.append("╔══════════════════════════════════════════╗\n", style="dim")
        out.append("║  LAST CALLS                              ║\n", style="bold white")
        out.append("╠══════════════════════════════════════════╣\n", style="dim")

        if not self.logs:
            out.append("║  No calls yet — run starter.py           ║\n", style="dim")
        else:
            for log in self.logs[:8]:
                ts = log["timestamp"][11:19]  # HH:MM:SS
                endpoint = log["endpoint"][:16].ljust(16)
                code = str(log["status_code"])
                code_style = "green" if log["status_code"] == 200 else "red"
                line = f"║  {log['method']:<4} {endpoint} "
                out.append(line, style="")
                out.append(f"{code} ", style=f"bold {code_style}")
                out.append(f"{ts}", style="dim")
                out.append(" " * max(0, 43 - len(line) - len(code) - 1 - len(ts)))
                out.append("║\n", style="dim")

        out.append("╚══════════════════════════════════════════╝", style="dim")
        return out

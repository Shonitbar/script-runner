from rich.text import Text
from textual.widget import Widget
from textual.reactive import reactive


class MissionsPanel(Widget):
    missions: reactive[list] = reactive([], layout=True)

    def render(self) -> Text:
        out = Text()
        out.append("╔══════════════════════════════════════════╗\n", style="dim")
        out.append("║  MISSIONS                                ║\n", style="bold white")
        out.append("╠══════════════════════════════════════════╣\n", style="dim")

        pending = [m for m in self.missions if not m["completed"]]
        done = [m for m in self.missions if m["completed"]]

        if not pending and not done:
            out.append("║  No missions available yet...            ║\n", style="dim")
        else:
            for m in pending:
                line = f"  > {m['name']}"
                reward = ""
                if m["reward_cycles"]:
                    reward += f" +{m['reward_cycles']:.0f}⚙"
                if m["reward_synth"]:
                    reward += f" +{m['reward_synth']}◈"
                line = f"║  > {m['name']:<22}{reward:<10}"
                out.append(line.ljust(43), style="yellow")
                out.append("║\n", style="dim")
                desc_line = f"║    {m['description'][:38]}"
                out.append(desc_line.ljust(43), style="dim")
                out.append("║\n", style="dim")

            if done:
                out.append("╠══════════════════════════════════════════╣\n", style="dim")
                out.append("║  COMPLETED                               ║\n", style="dim green")
                for m in done[-3:]:  # show last 3 completed
                    line = f"║  ✓ {m['name']}"
                    out.append(line.ljust(43), style="green")
                    out.append("║\n", style="dim")

        out.append("╚══════════════════════════════════════════╝", style="dim")
        return out

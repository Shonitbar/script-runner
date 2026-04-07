from rich.text import Text
from textual.widget import Widget
from textual.reactive import reactive

ZONE_COLORS = {
    "safe": "green",
    "caution": "yellow",
    "danger": "red",
    "critical": "bright_red",
}
ZONE_LABELS = {
    "safe": "SAFE",
    "caution": "CAUTION",
    "danger": "DANGER",
    "critical": "CRITICAL — MINING BLOCKED",
}


def _zone(entropy: float) -> str:
    if entropy >= 90:
        return "critical"
    if entropy >= 70:
        return "danger"
    if entropy >= 30:
        return "caution"
    return "safe"


class EntropyGauge(Widget):
    entropy: reactive[float] = reactive(0.0)

    def render(self) -> Text:
        zone = _zone(self.entropy)
        color = ZONE_COLORS[zone]
        label = ZONE_LABELS[zone]
        pct = self.entropy / 100.0

        # Wide bar — 38 chars
        width = 34
        filled = int(pct * width)
        bar = "█" * filled + "░" * (width - filled)

        # Risk zone markers
        #   safe|caution|danger|critical
        #   0   30      70     90     100
        markers = [" "] * width
        for threshold in [30, 70, 90]:
            idx = int(threshold / 100 * width)
            if idx < width:
                markers[idx] = "┃"
        marker_line = "".join(markers)

        out = Text()
        out.append("╔══════════════════════════════════════════╗\n", style="dim")
        out.append("║  ENTROPY GAUGE                           ║\n", style="bold white")
        out.append("╠══════════════════════════════════════════╣\n", style="dim")
        out.append(f"║  {self.entropy:5.1f}%  ", style="bold")
        out.append(label.ljust(32), style=f"bold {color}")
        out.append("║\n", style="dim")
        out.append("║  [", style="dim")
        out.append(bar, style=color)
        out.append("]    ║\n", style="dim")
        out.append("║   0% SAFE 30% CAUTION 70% DANGER 90%     ║\n", style="dim")
        out.append("╠══════════════════════════════════════════╣\n", style="dim")
        out.append("║  decay: -0.1/s idle  │  /compress -20e   ║\n", style="dim")
        out.append("╚══════════════════════════════════════════╝", style="dim")
        return out

from rich.text import Text
from textual.widget import Widget
from textual.reactive import reactive


ZONE_COLORS = {
    "safe": "green",
    "caution": "yellow",
    "danger": "red",
    "critical": "bright_red",
}

TIER_NAMES = {
    0: "BOOT SEQUENCE",
    1: "MANUAL LABOR",
    2: "SCRIPTING",
    3: "SYSTEMS",
}


def entropy_zone(entropy: float) -> str:
    if entropy >= 90:
        return "critical"
    if entropy >= 70:
        return "danger"
    if entropy >= 30:
        return "caution"
    return "safe"


def entropy_bar(entropy: float, width: int = 20) -> Text:
    zone = entropy_zone(entropy)
    color = ZONE_COLORS[zone]
    filled = int((entropy / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    return Text(bar, style=color)


class CorePanel(Widget):
    cycles: reactive[float] = reactive(0.0)
    entropy: reactive[float] = reactive(0.0)
    synth: reactive[int] = reactive(0)
    tier: reactive[int] = reactive(0)
    uptime: reactive[int] = reactive(0)
    cycle_multiplier: reactive[float] = reactive(1.0)
    overclock_active: reactive[bool] = reactive(False)
    overclock_remaining: reactive[int] = reactive(0)
    prestige_count: reactive[int] = reactive(0)
    dark_ops_unlocked: reactive[bool] = reactive(False)

    def render(self) -> Text:
        zone = entropy_zone(self.entropy)
        color = ZONE_COLORS[zone]
        tier_name = TIER_NAMES.get(self.tier, f"TIER {self.tier}")
        uptime_str = f"{self.uptime // 3600:02d}:{(self.uptime % 3600) // 60:02d}:{self.uptime % 60:02d}"
        mult_str = f"  x{self.cycle_multiplier:.1f}" if self.cycle_multiplier != 1.0 else ""
        oc_str = f"  ⚡OC {self.overclock_remaining}s" if self.overclock_active else ""

        out = Text()
        out.append("╔══════════════════════════════════════════╗\n", style="dim")
        out.append(f"║  SCRIPTRUNNER  v0.1   [{tier_name}]".ljust(43), style="bold green")
        out.append("║\n", style="dim")
        out.append("╠══════════════════════════════════════════╣\n", style="dim")
        out.append(f"║  ⚙  CYCLES    {self.cycles:>10.2f}{mult_str}{oc_str}".ljust(43))
        out.append("║\n", style="dim")
        # Entropy row 1: label | percentage  zone
        # prefix "  ⚡ ENTROPY  │  " = 17 display cols (⚡ is 2-wide)
        pct_str = f"{self.entropy:5.1f}%"
        zone_str = zone.upper()
        pad = 42 - 17 - len(pct_str) - 2 - len(zone_str)
        out.append("║", style="dim")
        out.append("  ⚡ ENTROPY     ", style="")
        out.append(pct_str, style=f"bold {color}")
        out.append("  ", style="")
        out.append(zone_str + " " * max(pad, 0), style=f"bold {color}")
        """
        #entropy bar
        out.append("║\n", style="dim")
        Entropy row 2: full-width bar (38 chars fills "  [bar]║")
        bar_width = 38
        filled = int((self.entropy / 100) * bar_width)
        bar_str = "█" * filled + "░" * (bar_width - filled)
        out.append("║  [", style="dim")
        out.append(bar_str, style=color)
        """
        out.append("║\n", style="dim")
        synth_line = f"{self.synth}/5"
        out.append(f"║  🔹 SYNTH     {synth_line:<27}", style="cyan")
        out.append("║\n", style="dim")
        out.append(f"║  ⏱  UPTIME    {uptime_str:<27}", style="dim")
        out.append("║\n", style="dim")
        if self.prestige_count > 0:
            prestige_str = f"♦️ PRESTIGE {self.prestige_count}  {'[DARK OPS]' if self.dark_ops_unlocked else ''}"
            out.append(f"║  {prestige_str:<40}", style="bold magenta")
            out.append("║\n", style="dim")
        out.append("╚══════════════════════════════════════════╝", style="dim")
        return out

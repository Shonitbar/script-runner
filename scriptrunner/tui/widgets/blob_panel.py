"""ENTITY — the blob companion widget. Grows and evolves based on player history."""

import random
from random import Random

from rich.text import Text
from textual.reactive import reactive
from textual.widget import Widget

# ── DNA gene pools ────────────────────────────────────────────────────────────

_EYES_POOL = ["·", "°", "◉", "■", ">", "^", "@", "★"]
_MOUTH_POOL = ["ω", "_", "-", "~", "^", "3"]
_LIMBS_POOL = ["/ \\", "╱ ╲", "~ ~", "{ }"]
_AURA_POOL = ["░▒▓", "·:∷", "▸▹▷", "⌐¬─"]
_SHAPE_POOL = ["ring", "scatter", "bracket"]
_COLOR_POOL = ["cyan", "magenta", "green", "yellow"]

_STAGE_NAMES = ["dormant", "stirring", "awakening", "evolving", "ascendant"]
_STAGE_THRESHOLDS = [0, 51, 201, 501, 2001]


def _get_stage(total: int) -> int:
    """Return stage 1–5 from total request count."""
    for i in range(4, 0, -1):
        if total >= _STAGE_THRESHOLDS[i]:
            return i + 1
    return 1


def _decode_dna(seed: int) -> dict:
    """Decode DNA seed into visual genes. Deterministic for a given seed."""
    rng = Random(seed)
    return {
        "eyes": rng.choice(_EYES_POOL),
        "mouth": rng.choice(_MOUTH_POOL),
        "limbs": rng.choice(_LIMBS_POOL),
        "aura": rng.choice(_AURA_POOL),
        "shape": rng.choice(_SHAPE_POOL),
        "color": rng.choice(_COLOR_POOL),
    }


_DEFAULT_DNA = {
    "eyes": "·",
    "mouth": "ω",
    "limbs": "/ \\",
    "aura": "░▒▓",
    "shape": "ring",
    "color": "cyan",
}


def _aura_char(dna: dict, entropy: float, dark: bool, chaos_rng: Random | None = None) -> str:
    """Pick the appropriate aura character based on entropy level and DNA."""
    chars = dna["aura"]
    if dark:
        # Dark ops players always get heavy aura
        aura_chars = "▓█"
        char = aura_chars[1] if entropy >= 70 else aura_chars[0]
    else:
        if entropy >= 90:
            # Chaotic — mix characters randomly
            pool = chars + "█"
            char = chaos_rng.choice(pool) if chaos_rng else pool[0]
        elif entropy >= 70:
            char = chars[min(2, len(chars) - 1)]
        elif entropy >= 30:
            char = chars[min(1, len(chars) - 1)]
        else:
            char = chars[0]
    return char


def _build_creature(
    stage: int,
    dna: dict,
    endpoints: list[str],
    entropy: float,
) -> list[str]:
    """
    Build the creature's ASCII art lines.
    Returns a list of plain strings (no Rich markup); caller handles styling.
    """
    has_eyes = "/mine" in endpoints
    has_mouth = "/status" in endpoints
    has_arms = "/compress" in endpoints
    has_body = "/automate" in endpoints
    has_overclock = "/overclock" in endpoints
    has_pipeline = "/pipeline" in endpoints
    has_dark = any(e.startswith("/dark-ops/") for e in endpoints)
    has_prestige = "/prestige" in endpoints

    eyes = dna["eyes"]
    if has_overclock and stage >= 3:
        eyes = "◉"  # Glowing upgrade

    mouth = dna["mouth"] if has_mouth else "·"
    left_arm, right_arm = dna["limbs"].split()

    # Build face string
    if not has_eyes:
        face = "(•)"
    elif not has_mouth:
        face = f"({eyes}·{eyes})"
    else:
        face = f"({eyes}{mouth}{eyes})"

    chaos_rng = Random(random.random()) if entropy >= 90 else None
    dark = has_dark

    aura = _aura_char(dna, entropy, dark, chaos_rng)

    # Determine aura width based on stage
    if stage <= 2:
        aura_pad = ""
    elif stage == 3:
        aura_pad = aura * 2
    elif stage == 4:
        aura_pad = aura * 3
    else:
        aura_pad = aura * 4

    lines: list[str] = []

    if stage == 1:
        # Tiny egg
        lines.append(f"      {face}      ")

    elif stage == 2:
        # Small face, no aura
        if has_prestige:
            lines.append("       ∧       ")
        lines.append(f"     {face}     ")

    elif stage == 3:
        # Face + sparse aura ring
        w = len(face) + len(aura_pad) * 2
        top = aura * (w + 2)
        if has_prestige:
            lines.append(f"  {aura * 2}  ∧  {aura * 2}  ")
        lines.append(f"  {top}  ")
        lines.append(f"  {aura_pad}{face}{aura_pad}  ")
        if has_arms:
            arms_line = f"{left_arm} {right_arm}"
            lines.append(f"  {aura_pad}{arms_line}{aura_pad}  ")
        lines.append(f"  {top}  ")

    elif stage == 4:
        # Creature with body + denser aura
        top = aura * (len(face) + len(aura_pad) * 2 + 2)
        if has_prestige:
            lines.append(f" {aura * 2}  ∧  {aura * 2} ")
        lines.append(f" {top} ")
        lines.append(f" {aura_pad}{face}{aura_pad} ")
        if has_arms and has_pipeline:
            lines.append(f" {aura_pad}{left_arm}|{right_arm}{aura_pad} ")
        elif has_arms:
            lines.append(f" {aura_pad}{left_arm} {right_arm}{aura_pad} ")
        if has_body:
            lines.append(f" {aura_pad}  |  {aura_pad} ")
        lines.append(f" {top} ")

    else:  # stage == 5
        # Full creature with rich aura
        top = aura * (len(face) + len(aura_pad) * 2 + 2)
        if has_prestige:
            lines.append(f"{aura * 3}  ∧  {aura * 3}")
        lines.append(f"{aura_pad}{top}{aura_pad}")
        lines.append(f"{aura_pad}{aura_pad}{face}{aura_pad}{aura_pad}")
        if has_arms and has_pipeline:
            lines.append(f"{aura_pad}{aura_pad}{left_arm}|{right_arm}{aura_pad}{aura_pad}")
        elif has_arms:
            lines.append(f"{aura_pad}{aura_pad}{left_arm} {right_arm}{aura_pad}{aura_pad}")
        if has_body:
            lines.append(f"{aura_pad}{aura_pad}  |  {aura_pad}{aura_pad}")
        lines.append(f"{aura_pad}{top}{aura_pad}")

    return lines


class BlobPanel(Widget):
    """Virtual companion widget — grows and evolves with the player's API history."""

    total_requests: reactive[int] = reactive(0)
    endpoints_seen: reactive[list] = reactive(list)
    dna_seed: reactive[int] = reactive(-1)
    entropy: reactive[float] = reactive(0.0)

    def render(self) -> Text:
        W = 44  # inner width (panel is 46 with borders)

        stage = _get_stage(self.total_requests)
        dna = _decode_dna(self.dna_seed) if self.dna_seed != -1 else _DEFAULT_DNA
        stage_name = _STAGE_NAMES[stage - 1]
        color = dna["color"]

        # Entropy-based aura color
        if self.entropy >= 90:
            aura_color = "bright_red"
        elif self.entropy >= 70:
            aura_color = "red"
        elif self.entropy >= 30:
            aura_color = "yellow"
        else:
            aura_color = color

        creature_lines = _build_creature(stage, dna, self.endpoints_seen, self.entropy)

        out = Text()

        # Top border
        out.append("╔" + "═" * W + "╗\n", style="dim")

        # Header
        title = "  ENTITY"
        stage_label = f"[{stage_name.upper()}]"
        header = title + "  " + stage_label
        padding = W - len(header)
        out.append("║", style="dim")
        out.append(f"  ENTITY", style=f"bold {color}")
        out.append(f"  {stage_label}", style="dim")
        out.append(" " * padding + "║\n", style="dim")

        # Separator
        out.append("╠" + "═" * W + "╣\n", style="dim")

        # Blank line
        out.append("║" + " " * W + "║\n", style="dim")

        # Creature lines — centered
        for line in creature_lines:
            padded = line.center(W)
            # Separate aura chars from creature chars for coloring
            row = Text()
            row.append("║", style="dim")
            for ch in padded:
                # Classify character
                if ch in "░▒▓█·:∷▸▹▷⌐¬─":
                    row.append(ch, style=aura_color)
                elif ch in "∧✦":
                    row.append(ch, style=f"bold {color}")
                elif ch in "()" + "".join(_EYES_POOL) + "".join(_MOUTH_POOL) + "/\\╱╲~{}|":
                    row.append(ch, style=f"bold {color}")
                else:
                    row.append(ch)
            row.append("║\n", style="dim")
            out.append_text(row)

        # Blank line
        out.append("║" + " " * W + "║\n", style="dim")

        # Footer — request count + stage name
        footer_text = f"  {self.total_requests} calls · {stage_name}"
        dna_label = f"DNA: {'???' if self.dna_seed == -1 else hex(self.dna_seed)[-6:]}"
        gap = W - len(footer_text) - len(dna_label) - 2
        out.append("║", style="dim")
        out.append(footer_text, style="dim")
        out.append(" " * max(0, gap), style="dim")
        out.append(dna_label + "  ", style=f"dim {color}")
        out.append("║\n", style="dim")

        # Bottom border
        out.append("╚" + "═" * W + "╝\n", style="dim")

        return out

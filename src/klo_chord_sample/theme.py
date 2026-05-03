"""
Color palette, fonts, and theme constants for the KLO Chord Sample GUI.
"""

import os, sys
from importlib import resources
from pathlib import Path

PACKAGE = "klo_chord_sample"

# ── Color palette ──────────────────────────────────────────────────────────────
COLOR_BG_LIGHT      = [25,  25,  33,  255]
COLOR_ACCENT        = [80,  170, 255, 255]
COLOR_ACCENT_GREEN  = [60,  210, 100, 255]
COLOR_ACCENT_ORANGE = [255, 160, 70,  255]
COLOR_TEXT          = [220, 220, 220, 255]
COLOR_TEXT_DIM      = [130, 130, 150, 255]
COLOR_STRING        = [190, 170, 130, 255]
COLOR_FRET          = [70,  70,  80,  255]
COLOR_DOT           = [210, 190, 150, 255]
COLOR_ROOT_DOT      = [255, 210, 50,  255]
COLOR_MUTED         = [200, 60,  60,  255]
COLOR_OPEN          = [60,  210, 100, 255]
COLOR_CHORD_BG      = [28,  28,  36,  255]
COLOR_CHORD_BORDER  = [59,  59,  64,  255]


def font_path() -> str:
    """Return the path to the bundled JetBrainsMono font."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return str(base / "assets" / "fonts" / "JetBrainsMono-Regular.ttf")
    return str(resources.files(PACKAGE).joinpath(
        "assets", "fonts", "JetBrainsMono-Regular.ttf"))

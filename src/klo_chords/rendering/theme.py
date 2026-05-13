"""
Color palette, fonts, and theme constants for the KLO Chords GUI.
"""

import sys
from importlib import resources
from pathlib import Path

PACKAGE = "klo_chords"

_draw_font = None

def set_draw_font(font_id) -> None:
    global _draw_font
    _draw_font = font_id

def get_draw_font():
    return _draw_font


def _frozen_base() -> Path | None:
    """
    Return the base directory when running as a PyInstaller bundle,
    or None otherwise (caller should fall back to importlib.resources).
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return None


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
COLOR_ACTIVE_SPEAKER   = [0,   230, 80,  255]
COLOR_INACTIVE_SPEAKER = [60,  60,  70,  255]


def _asset_path(subdir: str, filename: str) -> str:
    """Return the path to a bundled asset file."""
    base = _frozen_base()
    if base is not None:
        return str(base / "klo_chords" / "assets" / subdir / filename)
    return str(resources.files(PACKAGE).joinpath("assets", subdir, filename))


def font_path() -> str:
    """Return the path to the bundled DejaVu Sans font (full Unicode coverage)."""
    return _asset_path("fonts", "DejaVuSans.ttf")


def font_path_fallback() -> str:
    """Return the path to the JetBrains Mono fallback font."""
    return _asset_path("fonts", "JetBrainsMono-Regular.ttf")


def icon_path() -> str:
    """Return the path to the app icon."""
    return _asset_path("icons", "app_icon.ico")
# ── Waveform display mappings (shared by gui/app.py and state.py) ────────────
WAVE_INTERNAL_TO_DISPLAY = {
    "triangle": "Triangle",
    "sine": "Sine",
    "sawtooth": "Sawtooth",
}
WAVE_DISPLAY_NAMES = ["Triangle", "Sine", "Sawtooth"]

"""
PySide6 Theme & Styles Module for KLO Chords
--------------------------------------------
Ports the DPG theme (src/klo_chords/rendering/theme.py) to PySide6 equivalents:
  - All color constants as QColor objects
  - WAVE_INTERNAL_TO_DISPLAY and WAVE_DISPLAY_NAMES mappings
  - A dark QPalette
  - A comprehensive QSS stylesheet
  - apply_dark_theme() helper
  - A theme preview demo (run `python experiments/pyside6_theme.py`)

No dearpygui imports — pure PySide6.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Color Constants — Dark Theme (ported from DPG RGBA lists → QColor)
# ═══════════════════════════════════════════════════════════════════════════════

COLOR_BG_LIGHT        = QColor(25,  25,  33)
COLOR_ACCENT          = QColor(80,  170, 255)
COLOR_ACCENT_GREEN    = QColor(60,  210, 100)
COLOR_ACCENT_ORANGE   = QColor(255, 160, 70)
COLOR_TEXT            = QColor(220, 220, 220)
COLOR_TEXT_DIM        = QColor(130, 130, 150)
COLOR_STRING          = QColor(190, 170, 130)
COLOR_FRET            = QColor(70,  70,  80)
COLOR_DOT             = QColor(210, 190, 150)
COLOR_ROOT_DOT        = QColor(255, 210, 50)
COLOR_MUTED           = QColor(200, 60,  60)
COLOR_OPEN            = QColor(60,  210, 100)
COLOR_CHORD_BG        = QColor(28,  28,  36)
COLOR_CHORD_BORDER    = QColor(59,  59,  64)
COLOR_ACTIVE_SPEAKER  = QColor(0,   230, 80)
COLOR_INACTIVE_SPEAKER = QColor(60,  60,  70)
COLOR_MIDI_SPEAKER    = QColor(240, 200, 40)

# ── Derived / convenience colours (dark) ────────────────────────────────────
COLOR_WINDOW          = QColor(26,  26,  46)
COLOR_SURFACE         = QColor(42,  42,  62)
COLOR_SURFACE_HIGHER  = QColor(58,  58,  78)
COLOR_BORDER          = QColor(68,  68,  88)
COLOR_SCROLLBAR_BG    = QColor(35,  35,  50)
COLOR_SCROLLBAR_HANDLE = QColor(80,  80,  100)

# ═══════════════════════════════════════════════════════════════════════════════
# Color Constants — Earth-Tone Warm Theme
# ═══════════════════════════════════════════════════════════════════════════════

EARTH_BG              = QColor(245, 240, 232)   # #F5F0E8 warm cream
EARTH_SURFACE         = QColor(237, 228, 211)   # #EDE4D3 warm tan card
EARTH_SURFACE_HIGHER  = QColor(225, 214, 195)   # lighter warm tan
EARTH_ACCENT          = QColor(196, 115, 79)    # #C4734F terracotta/rust
EARTH_ACCENT_GREEN    = QColor(122, 154, 85)    # #7A9A55 warm olive green
EARTH_ACCENT_ORANGE   = QColor(232, 168, 80)    # #E8A850 warm amber
EARTH_ACCENT_GOLD     = QColor(232, 180, 80)    # #E8B450 warm gold/amber
EARTH_TEXT            = QColor(74,  55,  40)    # #4A3728 warm dark brown
EARTH_TEXT_DIM        = QColor(139, 115, 85)    # #8B7355 warm medium brown
EARTH_TEXT_DIMMER     = QColor(160, 140, 115)   # lighter warm brown
EARTH_BORDER          = QColor(212, 197, 176)   # #D4C5B0 warm tan
EARTH_BORDER_DARK     = QColor(180, 160, 135)   # darker warm tan
EARTH_SELECTION       = QColor(232, 168, 80)    # #E8A850 warm amber
EARTH_SCROLLBAR_BG    = QColor(235, 228, 218)   # warm cream variant
EARTH_SCROLLBAR_HANDLE = QColor(200, 185, 160)  # warm tan handle
EARTH_STRING          = QColor(139, 111, 78)    # #8B6F4E warm brown
EARTH_FRET            = QColor(196, 168, 130)   # #C4A882 warm tan
EARTH_DOT             = QColor(212, 197, 176)   # warm tan (#D4C5B0)
EARTH_ROOT_DOT        = QColor(232, 180, 80)    # #E8B450 warm gold
EARTH_ROOT_GREEN      = QColor(122, 154, 85)    # #7A9A55 warm olive green
EARTH_MUTED           = QColor(200, 80,  60)    # warm red
EARTH_OPEN            = QColor(122, 154, 85)    # warm olive green
EARTH_CHORD_BG        = QColor(237, 228, 211)   # #EDE4D3 warm tan card
EARTH_CHORD_BORDER    = QColor(212, 197, 176)   # #D4C5B0 warm tan
EARTH_ACTIVE_SPEAKER  = QColor(232, 168, 80)    # #E8A850 warm amber
EARTH_INACTIVE_SPEAKER = QColor(220, 212, 195)   # warm tan lighter
EARTH_MIDI_SPEAKER    = QColor(232, 180, 80)    # warm gold
EARTH_KEY_BORDER      = QColor(196, 168, 130)   # #C4A882 warm tan
EARTH_BLACK_KEY       = QColor(62,  46,  31)    # #3E2E1F dark warm brown
EARTH_WHITE_KEY       = QColor(255, 248, 236)   # #FFF8EC warm ivory
EARTH_SCALE_HIGHLIGHT = QColor(139, 181, 160)   # #8BB5A0 soft sage
EARTH_BASS_NOTE       = QColor(122, 154, 85)    # #7A9A55 warm olive green
EARTH_NUT_LINE        = QColor(90,  65,  45)    # darker warm brown
EARTH_HOVER           = QColor(232, 168, 80)    # warm amber outline
EARTH_FRET_MARKER     = QColor(180, 160, 135)   # warm tan marker
EARTH_START_FRET      = QColor(139, 115, 85)    # warm medium brown
EARTH_SUGG_BG         = QColor(245, 240, 225)   # warm cream suggestion bg

# ═══════════════════════════════════════════════════════════════════════════════
# Waveform display mappings  (mirror src/klo_chords/rendering/theme.py:72-78)
# ═══════════════════════════════════════════════════════════════════════════════

WAVE_INTERNAL_TO_DISPLAY: dict[str, str] = {
    "triangle": "Triangle",
    "sine":     "Sine",
    "sawtooth": "Sawtooth",
}

WAVE_DISPLAY_NAMES: list[str] = ["Triangle", "Sine", "Sawtooth"]

# ═══════════════════════════════════════════════════════════════════════════════
# Font stack  (JetBrainsMono → DejaVu Sans Mono → system monospace fallbacks)
# ═══════════════════════════════════════════════════════════════════════════════

_FONT_FAMILY = (
    '"JetBrains Mono", '
    '"DejaVu Sans Mono", '
    '"Consolas", '
    '"Courier New", '
    '"monospace"'
)

DEFAULT_FONT_FAMILY = _FONT_FAMILY


def _load_bundled_fonts() -> None:
    """Load JetBrains Mono and DejaVu Sans from the project assets/fonts directory.

    Called automatically by ``apply_dark_theme()`` and ``apply_earth_theme()``
    so the QSS font-family references resolve without system-wide installation.
    """
    import os as _os
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _fonts_dir = _os.path.join(_here, "..", "src", "klo_chords", "assets", "fonts")
    if not _os.path.isdir(_fonts_dir):
        return  # running from a different location; fonts may be installed system-wide
    for _ttf in ("JetBrainsMono-Regular.ttf", "DejaVuSans.ttf", "NotoSans-Regular.ttf"):
        _path = _os.path.join(_fonts_dir, _ttf)
        if _os.path.isfile(_path):
            QFontDatabase.addApplicationFont(_path)

# ═══════════════════════════════════════════════════════════════════════════════
# Dark QPalette
# ═══════════════════════════════════════════════════════════════════════════════


def dark_palette() -> QPalette:
    """Build and return a dark QPalette from the theme colour constants."""
    p = QPalette()

    # Window / general
    p.setColor(QPalette.ColorRole.Window,          COLOR_WINDOW)
    p.setColor(QPalette.ColorRole.WindowText,      COLOR_TEXT)
    p.setColor(QPalette.ColorRole.Base,            COLOR_SURFACE)
    p.setColor(QPalette.ColorRole.AlternateBase,   COLOR_CHORD_BG)
    p.setColor(QPalette.ColorRole.ToolTipBase,     COLOR_SURFACE)
    p.setColor(QPalette.ColorRole.ToolTipText,     COLOR_TEXT)
    p.setColor(QPalette.ColorRole.PlaceholderText, COLOR_TEXT_DIM)

    # Text
    p.setColor(QPalette.ColorRole.Text,            COLOR_TEXT)
    p.setColor(QPalette.ColorRole.BrightText,      COLOR_ACCENT)

    # Buttons
    p.setColor(QPalette.ColorRole.Button,          COLOR_SURFACE)
    p.setColor(QPalette.ColorRole.ButtonText,      COLOR_TEXT)

    # Highlights / selections
    p.setColor(QPalette.ColorRole.Highlight,       COLOR_ACCENT)
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

    # Links
    p.setColor(QPalette.ColorRole.Link,            COLOR_ACCENT)
    p.setColor(QPalette.ColorRole.LinkVisited,     COLOR_ACCENT.darker(120))

    # Disabled groups
    p.setColor(QPalette.ColorGroup.Disabled,
               QPalette.ColorRole.WindowText,      COLOR_TEXT_DIM)
    p.setColor(QPalette.ColorGroup.Disabled,
               QPalette.ColorRole.Text,            COLOR_TEXT_DIM)
    p.setColor(QPalette.ColorGroup.Disabled,
               QPalette.ColorRole.ButtonText,      COLOR_TEXT_DIM)

    return p


# ═══════════════════════════════════════════════════════════════════════════════
# Earth-Tone Warm QPalette
# ═══════════════════════════════════════════════════════════════════════════════


def earth_palette() -> QPalette:
    """Build and return a warm earth-tone QPalette."""
    p = QPalette()

    # Window / general
    p.setColor(QPalette.ColorRole.Window,          EARTH_BG)
    p.setColor(QPalette.ColorRole.WindowText,      EARTH_TEXT)
    p.setColor(QPalette.ColorRole.Base,            EARTH_SURFACE)
    p.setColor(QPalette.ColorRole.AlternateBase,   EARTH_CHORD_BG)
    p.setColor(QPalette.ColorRole.ToolTipBase,     EARTH_SURFACE)
    p.setColor(QPalette.ColorRole.ToolTipText,     EARTH_TEXT)
    p.setColor(QPalette.ColorRole.PlaceholderText, EARTH_TEXT_DIM)

    # Text
    p.setColor(QPalette.ColorRole.Text,            EARTH_TEXT)
    p.setColor(QPalette.ColorRole.BrightText,      EARTH_ACCENT)

    # Buttons
    p.setColor(QPalette.ColorRole.Button,          EARTH_SURFACE)
    p.setColor(QPalette.ColorRole.ButtonText,      EARTH_TEXT)

    # Highlights / selections
    p.setColor(QPalette.ColorRole.Highlight,       EARTH_SELECTION)
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    # Links
    p.setColor(QPalette.ColorRole.Link,            EARTH_ACCENT)
    p.setColor(QPalette.ColorRole.LinkVisited,     EARTH_ACCENT.darker(120))

    # Disabled groups
    p.setColor(QPalette.ColorGroup.Disabled,
               QPalette.ColorRole.WindowText,      EARTH_TEXT_DIM)
    p.setColor(QPalette.ColorGroup.Disabled,
               QPalette.ColorRole.Text,            EARTH_TEXT_DIM)
    p.setColor(QPalette.ColorGroup.Disabled,
               QPalette.ColorRole.ButtonText,      EARTH_TEXT_DIM)

    return p


# ═══════════════════════════════════════════════════════════════════════════════
# QSS Stylesheet — dark theme for the entire application
# ═══════════════════════════════════════════════════════════════════════════════

def _color(qcol: QColor) -> str:
    """Return a QColor as a CSS-compatible hex string (e.g. '#ffaa00')."""
    return qcol.name()


_QSS = f"""
/* ── Global defaults ─────────────────────────────────────────────────────── */

QMainWindow {{
    background-color: {_color(COLOR_WINDOW)};
}}

QWidget {{
    background-color: {_color(COLOR_WINDOW)};
    color: {_color(COLOR_TEXT)};
    font-family: {_FONT_FAMILY};
    font-size: 13px;
}}

/* ── QLabel ──────────────────────────────────────────────────────────────── */

QLabel {{
    background: transparent;
    color: {_color(COLOR_TEXT)};
    border: none;
}}

QLabel[dim="true"] {{
    color: {_color(COLOR_TEXT_DIM)};
}}

/* ── QComboBox ───────────────────────────────────────────────────────────── */

QComboBox {{
    background-color: {_color(COLOR_SURFACE)};
    color: {_color(COLOR_TEXT)};
    border: 1px solid {_color(COLOR_BORDER)};
    border-radius: 4px;
    padding: 4px 10px;
    min-width: 80px;
}}

QComboBox:hover {{
    border-color: {_color(COLOR_ACCENT)};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border: none;
    width: 0;
    height: 0;
}}

QComboBox QAbstractItemView {{
    background-color: {_color(COLOR_SURFACE)};
    color: {_color(COLOR_TEXT)};
    selection-background-color: {_color(COLOR_ACCENT)};
    selection-color: black;
    border: 1px solid {_color(COLOR_BORDER)};
    border-radius: 2px;
    outline: none;
}}

/* ── QPushButton ─────────────────────────────────────────────────────────── */

QPushButton {{
    background-color: {_color(COLOR_SURFACE)};
    color: {_color(COLOR_TEXT)};
    border: 1px solid {_color(COLOR_BORDER)};
    border-radius: 4px;
    padding: 6px 14px;
    min-width: 60px;
}}

QPushButton:hover {{
    background-color: {_color(COLOR_SURFACE_HIGHER)};
    border-color: {_color(COLOR_ACCENT)};
}}

QPushButton:pressed {{
    background-color: {_color(COLOR_ACCENT.darker(140))};
}}

QPushButton:disabled {{
    background-color: {_color(COLOR_CHORD_BG)};
    color: {_color(COLOR_TEXT_DIM)};
    border-color: {_color(COLOR_CHORD_BORDER)};
}}

QPushButton[accent="true"] {{
    background-color: {_color(COLOR_ACCENT)};
    color: black;
    font-weight: bold;
    border-color: {_color(COLOR_ACCENT)};
}}

QPushButton[accent="true"]:hover {{
    background-color: {_color(EARTH_ACCENT.lighter(110))};
}}

QPushButton[accent="true"]:pressed {{
    background-color: {_color(COLOR_ACCENT.darker(120))};
}}

/* ── QCheckBox ───────────────────────────────────────────────────────────── */

QCheckBox {{
    background: transparent;
    color: {_color(COLOR_TEXT)};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {_color(COLOR_BORDER)};
    border-radius: 3px;
    background-color: {_color(COLOR_SURFACE)};
}}

QCheckBox::indicator:hover {{
    border-color: {_color(COLOR_ACCENT)};
}}

QCheckBox::indicator:checked {{
    background-color: {_color(COLOR_ACCENT)};
    border-color: {_color(COLOR_ACCENT)};
}}

QCheckBox::indicator:disabled {{
    background-color: {_color(COLOR_CHORD_BG)};
    border-color: {_color(COLOR_CHORD_BORDER)};
}}

/* ── QSlider ─────────────────────────────────────────────────────────────── */

QSlider::groove:horizontal {{
    height: 6px;
    background-color: {_color(COLOR_CHORD_BG)};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    width: 14px;
    height: 14px;
    margin: -5px 0;
    background-color: {_color(COLOR_ACCENT)};
    border-radius: 7px;
    border: none;
}}

QSlider::handle:horizontal:hover {{
    background-color: {_color(EARTH_ACCENT.lighter(120))};
}}

QSlider::sub-page:horizontal {{
    background-color: {_color(COLOR_ACCENT)};
    border-radius: 3px;
}}

QSlider::groove:vertical {{
    width: 6px;
    background-color: {_color(COLOR_CHORD_BG)};
    border-radius: 3px;
}}

QSlider::handle:vertical {{
    width: 14px;
    height: 14px;
    margin: 0 -5px;
    background-color: {_color(COLOR_ACCENT)};
    border-radius: 7px;
    border: none;
}}

QSlider::handle:vertical:hover {{
    background-color: {_color(EARTH_ACCENT.lighter(120))};
}}

QSlider::sub-page:vertical {{
    background-color: {_color(COLOR_ACCENT)};
    border-radius: 3px;
}}

/* ── QTabWidget / QTabBar ────────────────────────────────────────────────── */

QTabWidget::pane {{
    border: 1px solid {_color(COLOR_BORDER)};
    border-radius: 4px;
    background-color: {_color(COLOR_WINDOW)};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {_color(COLOR_SURFACE)};
    color: {_color(COLOR_TEXT_DIM)};
    border: 1px solid {_color(COLOR_BORDER)};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 16px;
    margin-right: 2px;
}}

QTabBar::tab:hover {{
    color: {_color(COLOR_TEXT)};
    background-color: {_color(COLOR_SURFACE_HIGHER)};
}}

QTabBar::tab:selected {{
    color: {_color(COLOR_ACCENT)};
    background-color: {_color(COLOR_WINDOW)};
    border-bottom: 2px solid {_color(COLOR_ACCENT)};
}}

/* ── QScrollBar ──────────────────────────────────────────────────────────── */

QScrollBar:vertical {{
    background-color: {_color(COLOR_SCROLLBAR_BG)};
    width: 10px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {_color(COLOR_SCROLLBAR_HANDLE)};
    min-height: 30px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {_color(COLOR_ACCENT)};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
    border: none;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {_color(COLOR_SCROLLBAR_BG)};
    height: 10px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {_color(COLOR_SCROLLBAR_HANDLE)};
    min-width: 30px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {_color(COLOR_ACCENT)};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
    border: none;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* ── QGroupBox ───────────────────────────────────────────────────────────── */

QGroupBox {{
    color: {_color(COLOR_TEXT)};
    border: 1px solid {_color(COLOR_BORDER)};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    color: {_color(COLOR_ACCENT)};
}}

/* ── QLineEdit / QTextEdit / QSpinBox / QDoubleSpinBox ───────────────────── */

QLineEdit,
QTextEdit,
QPlainTextEdit,
QSpinBox,
QDoubleSpinBox {{
    background-color: {_color(COLOR_SURFACE)};
    color: {_color(COLOR_TEXT)};
    border: 1px solid {_color(COLOR_BORDER)};
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: {_color(COLOR_ACCENT)};
    selection-color: black;
}}

QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {{
    border-color: {_color(COLOR_ACCENT)};
}}

QSpinBox::up-button,
QDoubleSpinBox::up-button {{
    border: none;
    border-left: 1px solid {_color(COLOR_BORDER)};
    border-radius: 0;
    width: 18px;
}}

QSpinBox::down-button,
QDoubleSpinBox::down-button {{
    border: none;
    border-left: 1px solid {_color(COLOR_BORDER)};
    border-radius: 0;
    width: 18px;
}}

/* ── QToolTip ────────────────────────────────────────────────────────────── */

QToolTip {{
    background-color: {_color(COLOR_SURFACE)};
    color: {_color(COLOR_TEXT)};
    border: 1px solid {_color(COLOR_BORDER)};
    border-radius: 3px;
    padding: 4px 8px;
}}

/* ── QMenu ───────────────────────────────────────────────────────────────── */

QMenu {{
    background-color: {_color(COLOR_SURFACE)};
    color: {_color(COLOR_TEXT)};
    border: 1px solid {_color(COLOR_BORDER)};
    border-radius: 4px;
    padding: 4px 0;
}}

QMenu::item {{
    padding: 6px 24px;
}}

QMenu::item:selected {{
    background-color: {_color(COLOR_ACCENT)};
    color: black;
}}

QMenu::separator {{
    height: 1px;
    background-color: {_color(COLOR_BORDER)};
    margin: 4px 8px;
}}
"""





# ═══════════════════════════════════════════════════════════════════════════════
# QSS Stylesheet — earth-tone warm theme for the entire application
# ═══════════════════════════════════════════════════════════════════════════════

_QSS_EARTH = f"""
/* ── Global defaults ─────────────────────────────────────────────────────── */

QMainWindow {{
    background-color: {_color(EARTH_BG)};
}}

QWidget {{
    background-color: {_color(EARTH_BG)};
    color: {_color(EARTH_TEXT)};
    font-family: {_FONT_FAMILY};
    font-size: 13px;
}}

/* ── QLabel ──────────────────────────────────────────────────────────────── */

QLabel {{
    background: transparent;
    color: {_color(EARTH_TEXT)};
    border: none;
}}

QLabel[dim="true"] {{
    color: {_color(EARTH_TEXT_DIM)};
}}

/* ── QComboBox ───────────────────────────────────────────────────────────── */

QComboBox {{
    background-color: {_color(EARTH_SURFACE)};
    color: {_color(EARTH_TEXT)};
    border: 1px solid {_color(EARTH_BORDER)};
    border-radius: 4px;
    padding: 4px 10px;
    min-width: 80px;
}}

QComboBox:hover {{
    border-color: {_color(EARTH_ACCENT)};
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border: none;
    width: 0;
    height: 0;
}}

QComboBox QAbstractItemView {{
    background-color: {_color(EARTH_SURFACE)};
    color: {_color(EARTH_TEXT)};
    selection-background-color: {_color(EARTH_ACCENT)};
    selection-color: white;
    border: 1px solid {_color(EARTH_BORDER)};
    border-radius: 2px;
    outline: none;
}}

/* ── QPushButton ─────────────────────────────────────────────────────────── */

QPushButton {{
    background-color: {_color(EARTH_SURFACE)};
    color: {_color(EARTH_TEXT)};
    border: 1px solid {_color(EARTH_BORDER)};
    border-radius: 4px;
    padding: 6px 14px;
    min-width: 60px;
}}

QPushButton:hover {{
    background-color: {_color(EARTH_SURFACE_HIGHER)};
    border-color: {_color(EARTH_ACCENT)};
}}

QPushButton:pressed {{
    background-color: {_color(EARTH_ACCENT.darker(140))};
}}

QPushButton:disabled {{
    background-color: {_color(EARTH_CHORD_BG)};
    color: {_color(EARTH_TEXT_DIM)};
    border-color: {_color(EARTH_CHORD_BORDER)};
}}

QPushButton[accent="true"] {{
    background-color: {_color(EARTH_ACCENT)};
    color: white;
    font-weight: bold;
    border-color: {_color(EARTH_ACCENT)};
}}

QPushButton[accent="true"]:hover {{
    background-color: {_color(EARTH_ACCENT.lighter(110))};
}}

QPushButton[accent="true"]:pressed {{
    background-color: {_color(EARTH_ACCENT.darker(120))};
}}

/* ── QCheckBox ───────────────────────────────────────────────────────────── */

QCheckBox {{
    background: transparent;
    color: {_color(EARTH_TEXT)};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {_color(EARTH_BORDER)};
    border-radius: 3px;
    background-color: {_color(EARTH_SURFACE)};
}}



QCheckBox::indicator:hover {{
    border-color: {_color(EARTH_ACCENT)};
}}

QCheckBox::indicator:checked {{
    background-color: {_color(EARTH_ACCENT)};
    border-color: {_color(EARTH_ACCENT)};
}}

QCheckBox::indicator:disabled {{
    background-color: {_color(EARTH_CHORD_BG)};
    border-color: {_color(EARTH_CHORD_BORDER)};
}}

/* ── QSlider ─────────────────────────────────────────────────────────────── */

QSlider::groove:horizontal {{
    height: 6px;
    background-color: {_color(EARTH_CHORD_BG)};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    width: 14px;
    height: 14px;
    margin: -5px 0;
    background-color: {_color(EARTH_ACCENT)};
    border-radius: 7px;
    border: none;
}}

QSlider::handle:horizontal:hover {{
    background-color: {_color(EARTH_ACCENT.lighter(120))};
}}

QSlider::sub-page:horizontal {{
    background-color: {_color(EARTH_ACCENT)};
    border-radius: 3px;
}}

QSlider::groove:vertical {{
    width: 6px;
    background-color: {_color(EARTH_CHORD_BG)};
    border-radius: 3px;
}}

QSlider::handle:vertical {{
    width: 14px;
    height: 14px;
    margin: 0 -5px;
    background-color: {_color(EARTH_ACCENT)};
    border-radius: 7px;
    border: none;
}}

QSlider::handle:vertical:hover {{
    background-color: {_color(EARTH_ACCENT.lighter(120))};
}}

QSlider::sub-page:vertical {{
    background-color: {_color(EARTH_ACCENT)};
    border-radius: 3px;
}}


/* ── QTabWidget / QTabBar ────────────────────────────────────────────────── */

QTabWidget::pane {{
    border: 1px solid {_color(EARTH_BORDER)};
    border-radius: 4px;
    background-color: {_color(EARTH_BG)};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {_color(EARTH_SURFACE)};
    color: {_color(EARTH_TEXT_DIM)};
    border: 1px solid {_color(EARTH_BORDER)};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 6px 16px;
    margin-right: 2px;
}}

QTabBar::tab:hover {{
    color: {_color(EARTH_TEXT)};
    background-color: {_color(EARTH_SURFACE_HIGHER)};
}}

QTabBar::tab:selected {{
    color: {_color(EARTH_ACCENT)};
    background-color: {_color(EARTH_BG)};
    border-bottom: 2px solid {_color(EARTH_ACCENT)};
}}

/* ── QScrollBar ──────────────────────────────────────────────────────────── */

QScrollBar:vertical {{
    background-color: {_color(EARTH_SCROLLBAR_BG)};
    width: 10px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:vertical {{
    background-color: {_color(EARTH_SCROLLBAR_HANDLE)};
    min-height: 30px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {_color(EARTH_ACCENT)};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    background: none;
    border: none;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: {_color(EARTH_SCROLLBAR_BG)};
    height: 10px;
    margin: 0;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background-color: {_color(EARTH_SCROLLBAR_HANDLE)};
    min-width: 30px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {_color(EARTH_ACCENT)};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    background: none;
    border: none;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
}}

# ═══════════════════════════════════════════════════════════════════════════════

/* ── QGroupBox ───────────────────────────────────────────────────────────── */

QGroupBox {{
    color: {_color(EARTH_TEXT)};
    border: 1px solid {_color(EARTH_BORDER)};
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 8px;
    color: {_color(EARTH_ACCENT)};
}}

/* ── QLineEdit / QTextEdit / QSpinBox / QDoubleSpinBox ───────────────────── */

QLineEdit,
QTextEdit,
QPlainTextEdit,
QSpinBox,
QDoubleSpinBox {{
    background-color: {_color(EARTH_SURFACE)};
    color: {_color(EARTH_TEXT)};
    border: 1px solid {_color(EARTH_BORDER)};
    border-radius: 4px;
    padding: 4px 8px;
    selection-background-color: {_color(EARTH_ACCENT)};
    selection-color: white;
}}

QLineEdit:focus,
QTextEdit:focus,
QPlainTextEdit:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {{
    border-color: {_color(EARTH_ACCENT)};
}}

QSpinBox::up-button,
QDoubleSpinBox::up-button {{
    border: none;
    border-left: 1px solid {_color(EARTH_BORDER)};
    border-radius: 0;
    width: 18px;
}}

QSpinBox::down-button,
QDoubleSpinBox::down-button {{
    border: none;
    border-left: 1px solid {_color(EARTH_BORDER)};
    border-radius: 0;
    width: 18px;
}}

/* ── QToolTip ────────────────────────────────────────────────────────────── */

QToolTip {{
    background-color: {_color(EARTH_SURFACE)};
    color: {_color(EARTH_TEXT)};
    border: 1px solid {_color(EARTH_BORDER)};
    border-radius: 3px;
    padding: 4px 8px;
}}

/* ── QMenu ───────────────────────────────────────────────────────────────── */

QMenu {{
    background-color: {_color(EARTH_SURFACE)};
    color: {_color(EARTH_TEXT)};
    border: 1px solid {_color(EARTH_BORDER)};
    border-radius: 4px;
    padding: 4px 0;
}}

QMenu::item {{
    padding: 6px 24px;
}}

QMenu::item:selected {{
    background-color: {_color(EARTH_ACCENT)};
    color: white;
}}

QMenu::separator {{
    height: 1px;
    background-color: {_color(EARTH_BORDER)};
    margin: 4px 8px;
}}
"""

# Public API
# ═══════════════════════════════════════════════════════════════════════════════


def stylesheet() -> str:
    """Return the full dark-theme QSS stylesheet string."""
    return _QSS


def apply_dark_theme(app: QApplication) -> None:
    """Apply the dark palette + QSS stylesheet + default font to *app*."""
    _load_bundled_fonts()
    app.setStyle("Fusion")
    app.setPalette(dark_palette())
    app.setStyleSheet(_QSS)

    font = QFont()
    font.setFamilies([
        "JetBrains Mono",
        "DejaVu Sans Mono",
        "Consolas",
        "Courier New",
        "monospace",
    ])
    font.setPointSize(10)
    app.setFont(font)




def earth_stylesheet() -> str:
    """Return the full earth-tone QSS stylesheet string."""
    return _QSS_EARTH


def apply_earth_theme(app: QApplication) -> None:
    """Apply the earth-tone warm palette + QSS stylesheet + default font to *app*."""
    _load_bundled_fonts()
    app.setStyle("Fusion")
    app.setPalette(earth_palette())
    app.setStyleSheet(_QSS_EARTH)

    font = QFont()
    font.setFamilies([
        "JetBrains Mono",
        "DejaVu Sans Mono",
        "Consolas",
        "Courier New",
        "monospace",
    ])
    font.setPointSize(10)
    app.setFont(font)

# ═══════════════════════════════════════════════════════════════════════════════
# Theme preview demo
# ═══════════════════════════════════════════════════════════════════════════════


def demo() -> None:
    """Launch a small window exercising every themed widget for visual review."""
    app = QApplication.instance() or QApplication(sys.argv)
    apply_earth_theme(app)

    window = QMainWindow()
    window.setWindowTitle("PySide6 Theme — Preview")
    window.resize(640, 580)

    central = QWidget()
    window.setCentralWidget(central)
    root = QVBoxLayout(central)
    root.setSpacing(12)
    root.setContentsMargins(16, 16, 16, 16)

    # ── Header ────────────────────────────────────────────────────────────
    title = QLabel("KLO Chords — PySide6 Theme Preview")
    title.setStyleSheet(
        f"font-size:18px; font-weight:bold; "
        f"color:{EARTH_ACCENT.name()}; background:transparent;"
    )
    root.addWidget(title)

    dim_label = QLabel("This is a dim secondary text label")
    dim_label.setStyleSheet(
        f"color: {EARTH_TEXT_DIM.name()}; background: transparent;"
    )
    root.addWidget(dim_label)

    # ── Combo + Button row ────────────────────────────────────────────────
    row1 = QHBoxLayout()
    cb = QComboBox()
    cb.addItems(["Major", "Minor", "Harmonic Minor", "Dorian", "Phrygian"])
    cb.setCurrentText("Major")
    row1.addWidget(QLabel("Scale:"))
    row1.addWidget(cb)
    row1.addSpacing(16)

    btn_default = QPushButton("Default")
    row1.addWidget(btn_default)

    btn_accent = QPushButton("Accent")
    btn_accent.setStyleSheet(
        f"QPushButton {{ background-color: {EARTH_ACCENT.name()}; "
        f"color: black; font-weight: bold; "
        f"border: 1px solid {EARTH_ACCENT.name()}; "
        f"border-radius: 4px; padding: 6px 14px; }}"
        f"QPushButton:hover {{ "
        f"background-color: {EARTH_ACCENT.lighter(110).name()}; }}"
    )
    row1.addWidget(btn_accent)

    btn_disabled = QPushButton("Disabled")
    btn_disabled.setEnabled(False)
    row1.addWidget(btn_disabled)
    row1.addStretch()
    root.addLayout(row1)

    # ── Sliders ───────────────────────────────────────────────────────────
    row_slider = QHBoxLayout()
    row_slider.addWidget(QLabel("Volume:"))
    slider_h = QSlider(Qt.Orientation.Horizontal)
    slider_h.setValue(70)
    slider_h.setMaximum(100)
    row_slider.addWidget(slider_h, 1)
    root.addLayout(row_slider)

    # ── Checkboxes ────────────────────────────────────────────────────────
    row_cb = QHBoxLayout()
    cb1 = QCheckBox("Muted  (COLOR_MUTED)")
    cb1.setChecked(False)
    row_cb.addWidget(cb1)
    cb2 = QCheckBox("Open  (COLOR_OPEN)")
    cb2.setChecked(True)
    row_cb.addWidget(cb2)
    row_cb.addStretch()
    root.addLayout(row_cb)

    # ── Text inputs ───────────────────────────────────────────────────────
    le = QLineEdit()
    le.setPlaceholderText("QLineEdit — type something...")
    root.addWidget(le)

    spin = QSpinBox()
    spin.setRange(0, 12)
    spin.setValue(5)
    spin.setPrefix("Fret: ")
    root.addWidget(spin)


    # ── Tab widget ────────────────────────────────────────────────────────
    tabs = QTabWidget()
    tab1 = QWidget()
    tl1 = QVBoxLayout(tab1)
    tl1.addWidget(QLabel("Content in Tab 1"))
    tl1.addWidget(QPushButton("A button inside tab"))
    tl1.addStretch()
    tabs.addTab(tab1, "Fretboard")

    tab2 = QWidget()
    tl2 = QVBoxLayout(tab2)
    te = QTextEdit()
    te.setPlainText("QTextEdit with dark theme styling.\nLine 2.\nLine 3.")
    tl2.addWidget(te)
    tabs.addTab(tab2, "Log")
    root.addWidget(tabs)

    # ── Group box ─────────────────────────────────────────────────────────
    gb = QGroupBox("Chord Info")
    gl = QVBoxLayout(gb)
    gl.addWidget(QLabel("Root:  C"))
    gl.addWidget(QLabel("Quality:  Major"))
    gl.addWidget(QLabel("Notes:  C  E  G"))
    root.addWidget(gb)

    # ── Scrollable area ───────────────────────────────────────────────────
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setMaximumHeight(100)
    sw = QWidget()
    sl = QVBoxLayout(sw)
    for i in range(15):
        sl.addWidget(QLabel(f"Scroll item {i + 1} — scroll to see more"))
    sl.addStretch()
    sa.setWidget(sw)
    root.addWidget(sa)

    root.addStretch()

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    demo()

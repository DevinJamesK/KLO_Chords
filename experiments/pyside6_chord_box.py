"""
PySide6 Chord Box Widget - self-contained prototype matching the DPG version
(src/klo_chords/rendering/chord_box.py).

Features:
- ChordBoxWidget:  140x90px tile showing root + quality, notes, play bar, keybind
- ProgressionCellWidget: 88x78px grid cell with degree, name, notes, play bar, keybind
- Jazz chord symbols toggle (\u0394, \u00f8, \u2212) vs text (maj7, m7b5, min)
- Selection highlight with accent border
- Click interaction via chordClicked/progCellClicked signals
- Self-contained: run with `python experiments/pyside6_chord_box.py`
"""
from __future__ import annotations

import sys
import typing as t

from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import (
    QPainter, QFont, QColor, QPen, QBrush, QMouseEvent, QFontMetrics,
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QCheckBox, QFrame, QGridLayout, QPushButton,
)

# ============================================================================
# Colour palette (mirrors src/klo_chords/rendering/theme.py)
# ============================================================================
COLOR_BG_LIGHT        = QColor(245, 240, 232, 255)   # warm cream
COLOR_ACCENT          = QColor(196, 115, 79,  255)   # terracotta
COLOR_ACCENT_GREEN    = QColor(122, 154, 85,  255)   # warm olive green
COLOR_ACCENT_ORANGE   = QColor(232, 168, 80,  255)   # warm amber
COLOR_TEXT            = QColor(74,  55,  40,  255)   # warm dark brown
COLOR_TEXT_DIM        = QColor(139, 115, 85,  255)   # warm medium brown
COLOR_CHORD_BG        = QColor(237, 228, 211, 255)   # warm tan card
COLOR_CHORD_BORDER    = QColor(212, 197, 176, 255)   # warm tan
COLOR_ACTIVE_SPEAKER  = QColor(232, 168, 80,  255)   # warm amber
COLOR_INACTIVE_SPEAKER = QColor(220, 212, 195, 255)   # warm tan lighter
COLOR_SUGG_BG         = QColor(245, 240, 225, 255)   # warm cream suggestion bg

# ============================================================================
# Dimensions (match DPG chord_box.py)
# ============================================================================
CHORD_BOX_W = 140
CHORD_BOX_H = 90
PROG_CELL_W = 88
PROG_CELL_H = 78

# ============================================================================
# Keybind labels for chord cells (match DPG)
# ============================================================================
KEYBIND_LABELS = [
    "1", "2", "3", "4", "5", "6", "7", "8",           # Row 0
    "Q", "W", "E", "R", "T", "Y", "U", "I",           # Row 1
    "A", "S", "D", "F", "G", "H", "J", "K",           # Row 2
    "Z", "X", "C", "V", "B", "N", "M", ",",           # Row 3
]

# ============================================================================
# Quality maps (exported - match DPG chord_box.py)
# ============================================================================
PROG_QUALITY_NAMES = ["Major", "minor", "dim", "aug", "7", "m7", "maj7",
                      "dim7", "m7b5", "mmaj7", "aug7", "sus2", "sus4"]
PROG_QUALITY_MAP = {
    "Major": "M", "minor": "m", "dim": "dim", "aug": "aug",
    "7": "7", "m7": "m7", "maj7": "maj7",
    "dim7": "dim7", "m7b5": "m7b5", "mmaj7": "mmaj7", "aug7": "aug7",
    "sus2": "sus2", "sus4": "sus4",
}
PROG_QUALITY_REVERSE_MAP = {v: k for k, v in PROG_QUALITY_MAP.items()}


# ============================================================================
# Quality display helpers (mirrors src/klo_chords/core/quality.py)
# ============================================================================

def quality_symbol(quality: str) -> str:
    """Short chord quality suffix, e.g. 'min', 'min7', '\u25b37', '\u00b0'."""
    return {
        "M": "", "m": "min", "dim": "\u00b0", "aug": "+",
        "7": "7", "m7": "min7", "maj7": "\u25b37", "dim7": "\u00b07",
        "m7b5": "min7b5", "mmaj7": "min\u25b37", "aug7": "+7",
        "augmaj7": "+\u25b37",
        "sus2": "sus2", "sus4": "sus4",
    }.get(quality, quality)


def quality_symbol_jazz(quality: str) -> str:
    """Jazz chord quality suffix using standard glyphs: \u2212 \u25b3 \u00f8."""
    return {
        "M": "\u25b3", "m": "\u2212", "dim": "\u00b0", "aug": "+",
        "7": "7", "m7": "\u22127", "maj7": "\u25b37", "dim7": "\u00b07",
        "m7b5": "\u00f8", "mmaj7": "\u2212\u25b37", "aug7": "+7",
        "augmaj7": "+\u25b37",
        "sus2": "sus2", "sus4": "sus4",
    }.get(quality, quality)


def get_quality_display(quality: str, jazz: bool = False) -> str:
    """Return the appropriate quality symbol based on display mode."""
    if jazz:
        return quality_symbol_jazz(quality)
    return quality_symbol(quality)


# ============================================================================
# Degree computation helper (mirrors src/klo_chords/core/chords.py)
# ============================================================================

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

ENHARMONIC = {
    'C#': 'Db', 'D#': 'Eb', 'F#': 'Gb', 'G#': 'Ab', 'A#': 'Bb',
    'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#',
}

KEY_PREFERRED_ACCIDENTAL = {
    'F':  'flat', 'Bb': 'flat', 'Eb': 'flat', 'Ab': 'flat',
    'Db': 'flat', 'Gb': 'flat', 'Cb': 'flat',
    'G':  'sharp', 'D':  'sharp', 'A':  'sharp', 'E':  'sharp',
    'B':  'sharp', 'F#': 'sharp', 'C#': 'sharp',
}
KEY_PREFERRED_ACCIDENTAL.setdefault('C', 'flat')

_SCALE_INTERVALS = {
    "Major":          [0, 2, 4, 5, 7, 9, 11],
    "Natural minor":  [0, 2, 3, 5, 7, 8, 10],
    "Harmonic minor": [0, 2, 3, 5, 7, 8, 11],
    "Melodic minor":  [0, 2, 3, 5, 7, 9, 11],
    "Pentatonic Maj": [0, 2, 4, 7, 9],
    "Pentatonic min": [0, 3, 5, 7, 10],
    "Blues":          [0, 3, 5, 6, 7, 10],
    "Dorian":         [0, 2, 3, 5, 7, 9, 10],
    "Phrygian":       [0, 1, 3, 5, 7, 8, 10],
    "Lydian":         [0, 2, 4, 6, 7, 9, 11],
    "Mixolydian":     [0, 2, 4, 5, 7, 9, 10],
    "Locrian":        [0, 1, 3, 5, 6, 8, 10],
}


def _note_to_pc(note: str) -> int:
    note = note.strip()
    for pc, name in enumerate(NOTE_NAMES):
        if name == note:
            return pc
        if note in ENHARMONIC and ENHARMONIC[note] == name:
            return pc
    raise ValueError(f"Unknown note: {note}")


def _pc_to_note(pc: int, style: str = "sharp") -> str:
    name = NOTE_NAMES[pc % 12]
    if style == "flat" and '#' in name:
        return ENHARMONIC[name]
    return name


def _heptatonic_degree_names(scale_name: str) -> list:
    if scale_name == "Major":
        return ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii\u00b0']
    return ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii']


def _get_accidental_style(root_note: str) -> str:
    root_clean = root_note.replace('m', '').replace('-', '')
    return KEY_PREFERRED_ACCIDENTAL.get(root_clean, 'sharp')


def get_degree_for_root(root: str, key: str, scale_name: str) -> str:
    """Return the roman numeral for *root* relative to *key*/*scale_name*."""
    root_pc = _note_to_pc(root)
    key_pc = _note_to_pc(key)
    intervals = _SCALE_INTERVALS.get(scale_name)
    if not intervals:
        return ""
    scale_pitches = [(key_pc + i) % 12 for i in intervals]
    degree_names = _heptatonic_degree_names(scale_name)
    if len(scale_pitches) != len(degree_names):
        degree_names = [
            f"{' I II III IV V VI VII'[i]}"
            for i in range(len(scale_pitches))
        ]

    root_clean = root.strip().upper()
    letter = root_clean[0]
    has_flat = 'B' in root_clean[1:]
    has_sharp = '#' in root_clean[1:]

    for i, pc in enumerate(scale_pitches):
        natural_name = _pc_to_note(pc, _get_accidental_style(key))
        if natural_name[0].upper() == letter:
            degree = degree_names[i] if i < len(degree_names) else f"^{i+1}"
            if has_flat:
                return "\u266d" + degree
            elif has_sharp:
                return "\u266f" + degree
            else:
                return degree

    best_dist = 12
    best_i = 0
    for i, pc in enumerate(scale_pitches):
        dist = min((root_pc - pc) % 12, (pc - root_pc) % 12)
        if dist < best_dist:
            best_dist = dist
            best_i = i
    if best_dist >= 12:
        return ""

    degree = degree_names[best_i] if best_i < len(degree_names) else f"^{best_i+1}"
    scale_pc = scale_pitches[best_i]
    if (root_pc - scale_pc) % 12 <= 6:
        return "\u266f" + degree
    else:
        return "\u266d" + degree


# ============================================================================
# ChordBoxWidget - large tile (140x90)
# ============================================================================

class ChordBoxWidget(QWidget):
    """A 140x90px painted chord tile.

    Shows the chord name (root + quality symbol), chord notes,
    an optional play bar at the bottom, and an optional keybind label
    in the top-right corner. Supports selection highlighting and
    jazz/standard symbol toggling.

    Signals
    -------
    chordClicked(int)
        Emitted with the widget's *index* when the widget is clicked.
    """

    chordClicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._index = 0
        self._root = "C"
        self._quality = "M"
        self._notes = ["C", "E", "G"]
        self._selected = False
        self._show_keybind = False
        self._keybind_label = ""
        self._use_jazz_symbols = False
        self._show_play_bar = False
        self.setFixedSize(CHORD_BOX_W, CHORD_BOX_H)
        self.setMouseTracking(True)

    # -- public setters ------------------------------------------------------

    def set_index(self, idx):
        self._index = idx

    def set_chord(self, root, quality, notes):
        self._root = root
        self._quality = quality
        self._notes = notes
        self.update()

    def set_selected(self, selected):
        self._selected = selected
        self.update()

    def set_show_keybind(self, show):
        self._show_keybind = show
        self.update()

    def set_keybind_label(self, label):
        self._keybind_label = label
        self.update()

    def set_use_jazz_symbols(self, jazz):
        self._use_jazz_symbols = jazz
        self.update()

    def set_show_play_bar(self, show):
        self._show_play_bar = show
        self.update()

    # -- painting ------------------------------------------------------------

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # Background + border
        border_col = COLOR_ACCENT if self._selected else COLOR_CHORD_BG
        border_thick = 2 if self._selected else 0
        p.setPen(QPen(border_col, border_thick))
        p.setBrush(QBrush(COLOR_CHORD_BG))
        p.drawRect(QRect(0, 0, w - 1, h - 1))

        # Play bar at bottom
        if self._show_play_bar:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(COLOR_ACTIVE_SPEAKER))
            p.drawRect(QRect(2, h - 8, w - 5, 5))

        # Chord title: root + quality
        q = get_quality_display(self._quality, self._use_jazz_symbols).strip()
        title = self._root + (" " + q if q else "")
        title_col = COLOR_ACCENT if self._selected else COLOR_TEXT
        font_title = QFont("Consolas", 20, QFont.Weight.Bold)
        p.setFont(font_title)
        p.setPen(title_col)
        fm = QFontMetrics(font_title)
        p.drawText(8, 10 + fm.ascent(), title)

        # Notes
        notes_str = " ".join(self._notes)
        font_notes = QFont("Consolas", 15)
        p.setFont(font_notes)
        p.setPen(COLOR_TEXT_DIM)
        fm2 = QFontMetrics(font_notes)
        p.drawText(8, 40 + fm2.ascent(), notes_str)

        # Keybind label in top-right corner
        if self._show_keybind:
            lbl = self._keybind_label
            if not lbl and self._index < len(KEYBIND_LABELS):
                lbl = KEYBIND_LABELS[self._index]
            if lbl:
                font_kb = QFont("Consolas", 11)
                p.setFont(font_kb)
                p.setPen(COLOR_TEXT_DIM)
                fm3 = QFontMetrics(font_kb)
                lbl_w = fm3.horizontalAdvance(lbl)
                p.drawText(int(w - 8 - lbl_w), 4 + fm3.ascent(), lbl)

        p.end()

    # -- interaction ---------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.chordClicked.emit(self._index)


# ============================================================================
# ProgressionCellWidget - compact grid cell (88x78)
# ============================================================================

class ProgressionCellWidget(QWidget):
    """A compact 88x78px progression grid cell.

    Shows the degree symbol (Roman numeral), chord name, notes,
    play bar at the bottom, and optionally a keybind label.
    Supports empty state, selection highlighting, and custom
    background colours.

    Signals
    -------
    progCellClicked(int)
        Emitted with the widget's *index* when the widget is clicked.
    """

    progCellClicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._index = 0
        self._root = None
        self._quality = "M"
        self._notes = []
        self._key = "C"
        self._scale = "Major"
        self._selected = False
        self._show_keybind = False
        self._keybind_label = ""
        self._use_jazz_symbols = False
        self._show_play_bar = False
        self._bg_color = None
        self.setFixedSize(PROG_CELL_W, PROG_CELL_H)
        self.setMouseTracking(True)

    # -- public setters ------------------------------------------------------

    def set_index(self, idx):
        self._index = idx

    def set_cell(self, root, quality, notes, key="C", scale="Major"):
        self._root = root
        self._quality = quality
        self._notes = notes
        self._key = key
        self._scale = scale
        self.update()

    def set_selected(self, selected):
        self._selected = selected
        self.update()

    def set_show_keybind(self, show):
        self._show_keybind = show
        self.update()

    def set_keybind_label(self, label):
        self._keybind_label = label
        self.update()

    def set_use_jazz_symbols(self, jazz):
        self._use_jazz_symbols = jazz
        self.update()

    def set_show_play_bar(self, show):
        self._show_play_bar = show
        self.update()

    def set_bg_color(self, color):
        self._bg_color = color
        self.update()

    def clear(self):
        self._root = None
        self._notes = []
        self.update()

    @property
    def is_empty(self):
        return self._root is None

    # -- painting ------------------------------------------------------------

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # Background and border
        fill_col = self._bg_color if self._bg_color is not None else COLOR_CHORD_BG
        border_col = COLOR_ACCENT if self._selected else COLOR_CHORD_BORDER
        border_thick = 2 if self._selected else 1
        p.setPen(QPen(border_col, border_thick))
        p.setBrush(QBrush(fill_col))
        p.drawRect(QRect(0, 0, w - 1, h - 1))

        # Play bar at bottom
        if self._show_play_bar:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(COLOR_ACTIVE_SPEAKER))
            p.drawRect(QRect(2, h - 6, w - 5, 4))

        # Keybind label (top-right)
        if self._show_keybind:
            lbl = self._keybind_label
            if not lbl and self._index < len(KEYBIND_LABELS):
                lbl = KEYBIND_LABELS[self._index]
            if lbl:
                font_kb = QFont("Consolas", 9)
                p.setFont(font_kb)
                p.setPen(COLOR_TEXT_DIM)
                fm = QFontMetrics(font_kb)
                lbl_w = fm.horizontalAdvance(lbl)
                lbl_x = w - 8 - lbl_w
                p.drawText(int(lbl_x), 3 + fm.ascent(), lbl)

        # Empty state
        if self._root is None:
            font_empty = QFont("Consolas", 12)
            p.setFont(font_empty)
            p.setPen(COLOR_TEXT_DIM)
            fm_e = QFontMetrics(font_empty)
            empty_text = "Empty"
            empty_w = fm_e.horizontalAdvance(empty_text)
            p.drawText(int((w - empty_w) / 2), int(h / 2 + fm_e.ascent() / 3),
                       empty_text)
            p.end()
            return

        # Degree symbol (left, near top)
        try:
            degree = get_degree_for_root(self._root, self._key, self._scale)
        except (ValueError, KeyError):
            degree = "?"
        font_deg = QFont("Consolas", 12, QFont.Weight.Bold)
        p.setFont(font_deg)
        p.setPen(COLOR_ACCENT)
        fm_d = QFontMetrics(font_deg)
        p.drawText(5, 3 + fm_d.ascent(), degree)

        # Chord name
        q = get_quality_display(self._quality, self._use_jazz_symbols).strip()
        name = self._root + (" " + q if q else "")
        font_name = QFont("Consolas", 14, QFont.Weight.Bold)
        p.setFont(font_name)
        p.setPen(COLOR_TEXT)
        fm_n = QFontMetrics(font_name)
        p.drawText(5, 20 + fm_n.ascent(), name)

        # Notes
        notes_str = " ".join(self._notes)
        font_notes = QFont("Consolas", 11)
        p.setFont(font_notes)
        p.setPen(COLOR_TEXT_DIM)
        fm_nt = QFontMetrics(font_notes)
        p.drawText(5, 44 + fm_nt.ascent(), notes_str)

        p.end()

    # -- interaction ---------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.progCellClicked.emit(self._index)


# ============================================================================
# Demo / test harness
# ============================================================================

class ChordBoxDemo(QMainWindow):
    """Demo window showing ChordBoxWidget and ProgressionCellWidget."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Chord Box - Demo")
        self.setMinimumSize(900, 600)
        self.resize(960, 640)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # -- Global toggles --------------------------------------------------
        toggle_row = QHBoxLayout()

        self._jazz_cb = QCheckBox("Use jazz symbols (triangle dash o)")
        self._jazz_cb.setChecked(False)
        self._jazz_cb.toggled.connect(self._on_jazz_toggle)
        toggle_row.addWidget(self._jazz_cb)

        self._keybind_cb = QCheckBox("Show keybinds")
        self._keybind_cb.setChecked(True)
        self._keybind_cb.toggled.connect(self._on_keybind_toggle)
        toggle_row.addWidget(self._keybind_cb)

        info_lbl = QLabel("Click a chord tile to select it (border turns blue)")
        info_lbl.setStyleSheet("color:#8B7355; font-size:10px;")
        toggle_row.addWidget(info_lbl)
        toggle_row.addStretch()

        main_layout.addLayout(toggle_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#D4C5B0;")
        main_layout.addWidget(sep)

        # -- ChordBoxWidget row ----------------------------------------------
        lbl_chords = QLabel("ChordBoxWidget (140x90) - Diatonic triads in C Major")
        lbl_chords.setStyleSheet(
            "font-weight:bold; color:#8B7355; background:transparent;")
        main_layout.addWidget(lbl_chords)

        chords_row = QHBoxLayout()
        chords_row.setSpacing(6)

        sample_chords = [
            ("C",  "M",   ["C",  "E",  "G"]),
            ("D",  "m",   ["D",  "F",  "A"]),
            ("E",  "m",   ["E",  "G",  "B"]),
            ("F",  "M",   ["F",  "A",  "C"]),
            ("G",  "M",   ["G",  "B",  "D"]),
            ("A",  "m",   ["A",  "C",  "E"]),
            ("B",  "dim", ["B",  "D",  "F"]),
        ]

        self._chord_widgets = []
        self._selected_chord = -1

        for i, (root, quality, notes) in enumerate(sample_chords):
            cw = ChordBoxWidget()
            cw.set_index(i)
            cw.set_chord(root, quality, notes)
            cw.set_show_keybind(True)
            cw.set_keybind_label(KEYBIND_LABELS[i])
            cw.chordClicked.connect(self._on_chord_clicked)
            self._chord_widgets.append(cw)
            chords_row.addWidget(cw)

        chords_row.addStretch()
        main_layout.addLayout(chords_row)

        # -- Info label for selected chord -----------------------------------
        self._chord_info = QLabel("Selected chord: (none)")
        self._chord_info.setStyleSheet(
            "color:#8B7355; font-size:10px; background:transparent;")
        main_layout.addWidget(self._chord_info)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("color:#D4C5B0;")
        main_layout.addWidget(sep2)

        # -- ProgressionCellWidget grid --------------------------------------
        lbl_prog = QLabel(
            "ProgressionCellWidget (88x78) - I-IV-V-I with degree computation")
        lbl_prog.setStyleSheet(
            "font-weight:bold; color:#8B7355; background:transparent;")
        main_layout.addWidget(lbl_prog)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(3)

        prog_cells_data = [
            ("C",  "M",   ["C", "E", "G"]),     # I
            ("F",  "M",   ["F", "A", "C"]),     # IV
            ("G",  "M",   ["G", "B", "D"]),     # V
            ("C",  "M",   ["C", "E", "G"]),     # I
            ("A",  "m",   ["A", "C", "E"]),     # vi
            ("D",  "m",   ["D", "F", "A"]),     # ii
            ("B",  "dim", ["B", "D", "F"]),     # vii deg
            (None, "M",   []),                     # empty
        ]

        self._prog_widgets = []
        self._selected_prog = -1

        for i, (root, quality, notes) in enumerate(prog_cells_data):
            pw = ProgressionCellWidget()
            pw.set_index(i)
            pw.set_cell(root, quality, notes, key="C", scale="Major")
            pw.set_show_keybind(True)
            pw.set_keybind_label(KEYBIND_LABELS[i])
            # Custom bg for the first cell (simulates "suggestion original")
            if i == 0:
                pw.set_bg_color(COLOR_SUGG_BG)
            pw.progCellClicked.connect(self._on_prog_clicked)
            self._prog_widgets.append(pw)
            row, col = divmod(i, 4)
            grid_layout.addWidget(pw, row, col)

        main_layout.addLayout(grid_layout)

        self._prog_info = QLabel("Selected progression cell: (none)")
        self._prog_info.setStyleSheet(
            "color:#8B7355; font-size:10px; background:transparent;")
        main_layout.addWidget(self._prog_info)

        # -- Play bar test button --------------------------------------------
        btn_row = QHBoxLayout()
        self._play_btn = QPushButton("Toggle Play Bar (chord 0)")
        self._play_btn.clicked.connect(self._toggle_play_bar)
        btn_row.addWidget(self._play_btn)
        btn_row.addStretch()
        main_layout.addLayout(btn_row)

        main_layout.addStretch()

        # Dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #F5F0E8; }
            QWidget { background-color: #F5F0E8; color: #4A3728; }
            QLabel { background: transparent; }
            QCheckBox { color: #4A3728; background: transparent; spacing: 6px; }
            QCheckBox::indicator { width: 14px; height: 14px; }
            QPushButton {
                background-color: #EDE4D3; color: #4A3728;
                border: 1px solid #D4C5B0; border-radius: 4px;
                padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background-color: #E1D6C3; }
        """)

    # -- slots ---------------------------------------------------------------

    def _on_jazz_toggle(self, checked):
        for w in self._chord_widgets:
            w.set_use_jazz_symbols(checked)
        for w in self._prog_widgets:
            w.set_use_jazz_symbols(checked)

    def _on_keybind_toggle(self, checked):
        for w in self._chord_widgets:
            w.set_show_keybind(checked)
        for w in self._prog_widgets:
            w.set_show_keybind(checked)

    def _on_chord_clicked(self, idx):
        if 0 <= self._selected_chord < len(self._chord_widgets):
            self._chord_widgets[self._selected_chord].set_selected(False)
        self._selected_chord = idx
        if 0 <= idx < len(self._chord_widgets):
            self._chord_widgets[idx].set_selected(True)
            w = self._chord_widgets[idx]
            q = get_quality_display(w._quality, w._use_jazz_symbols).strip()
            name = w._root + (" " + q if q else "")
            self._chord_info.setText(
                f"Selected chord: {name}  |  notes: {' '.join(w._notes)}")

    def _on_prog_clicked(self, idx):
        if 0 <= self._selected_prog < len(self._prog_widgets):
            self._prog_widgets[self._selected_prog].set_selected(False)
        self._selected_prog = idx
        if 0 <= idx < len(self._prog_widgets):
            pw = self._prog_widgets[idx]
            pw.set_selected(True)
            if pw.is_empty:
                self._prog_info.setText(
                    f"Selected progression cell: [{idx}] - Empty")
            else:
                try:
                    deg = get_degree_for_root(pw._root, pw._key, pw._scale)
                except (ValueError, KeyError):
                    deg = "?"
                q = get_quality_display(
                    pw._quality, pw._use_jazz_symbols).strip()
                name = pw._root + (" " + q if q else "")
                self._prog_info.setText(
                    f"Selected progression cell: [{idx}] {deg} {name}"
                    f"  |  {' '.join(pw._notes)}")

    def _toggle_play_bar(self):
        if self._chord_widgets:
            current = self._chord_widgets[0]._show_play_bar
            self._chord_widgets[0].set_show_play_bar(not current)
            if self._prog_widgets:
                self._prog_widgets[0].set_show_play_bar(not current)


# ============================================================================
# Entry point
# ============================================================================

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor("#F5F0E8"))
    palette.setColor(palette.ColorRole.WindowText, QColor("#4A3728"))
    palette.setColor(palette.ColorRole.Base, QColor("#EDE4D3"))
    palette.setColor(palette.ColorRole.Text, QColor("#4A3728"))
    app.setPalette(palette)

    demo = ChordBoxDemo()
    demo.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

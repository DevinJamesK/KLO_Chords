"""
Chord name box drawn on a Dear PyGui drawlist.
Shows root + quality and notes in a compact tile.
Degree is rendered in a separate column to the left.
Also provides the compact progression grid cell renderer.
"""

import dearpygui.dearpygui as dpg
from klo_chords.chords import ChordInfo, ProgCell
from klo_chords.quality import quality_symbol
from klo_chords.theme import (
    COLOR_ACCENT, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_CHORD_BG, COLOR_CHORD_BORDER,
    COLOR_ACTIVE_SPEAKER, COLOR_INACTIVE_SPEAKER, COLOR_BG_LIGHT,
)

# ── Keybind labels for chord cells ──────────────────────────────────────────────
# Chords tab: 1-7 for the 7 diatonic chords
# Progression tab: 28 cells mapped to keyboard rows
KEYBIND_LABELS = [
    "1", "2", "3", "4", "5", "6", "7", "8",           # Row 0
    "Q", "W", "E", "R", "T", "Y", "U", "I",           # Row 1
    "A", "S", "D", "F", "G", "H", "J", "K",           # Row 2
    "Z", "X", "C", "V", "B", "N", "M", ",",           # Row 3
]


CHORD_BOX_W = 140
CHORD_BOX_H = 90

# ── Progression grid cell dimensions ──────────────────────────────────────────
PROG_CELL_W = 88
PROG_CELL_H = 78

# Quality names for progression cell detail combo (display names with internal mapping)
PROG_QUALITY_NAMES = ["Major", "minor", "dim", "aug", "7", "m7", "maj7",
                      "dim7", "m7b5", "mmaj7", "aug7", "sus2", "sus4"]
PROG_QUALITY_MAP = {
    "Major": "M", "minor": "m", "dim": "dim", "aug": "aug",
    "7": "7", "m7": "m7", "maj7": "maj7",
    "dim7": "dim7", "m7b5": "m7b5", "mmaj7": "mmaj7", "aug7": "aug7",
    "sus2": "sus2", "sus4": "sus4",
}
PROG_QUALITY_REVERSE_MAP = {v: k for k, v in PROG_QUALITY_MAP.items()}



def draw_chord_label(canvas_tag: str, chord: ChordInfo, idx: int,
                     selected: bool = False, show_keybind: bool = False):
    """Redraw the chord name tile inside *canvas_tag*.
    Degree is shown in a separate column outside this drawlist.
    Selection highlighting is handled externally by state._select_chord()
    via configure_item on the border/title tags.
    If *show_keybind* is True, the key shortcut (e.g. "1".."7") is drawn
    in the top‑right corner.
    """
    dpg.delete_item(canvas_tag, children_only=True)
    q = quality_symbol(chord.quality).strip()
    if q:
        title = chord.root + " " + q
    else:
        title = chord.root
    notes = "(" + " ".join(chord.notes) + ")"
    border_col   = COLOR_ACCENT               if selected else COLOR_CHORD_BG
    border_thick = 2                          if selected else 0
    title_col    = COLOR_ACCENT               if selected else COLOR_TEXT
    dpg.draw_rectangle([0, 0],
                       [CHORD_BOX_W - 1, CHORD_BOX_H - 1],
                       fill=COLOR_CHORD_BG, color=border_col,
                       thickness=border_thick,
                       tag="chord_border_" + str(idx), parent=canvas_tag)
    dpg.draw_rectangle([2, CHORD_BOX_H - 8], [CHORD_BOX_W - 3, CHORD_BOX_H - 3],
                       fill=COLOR_ACTIVE_SPEAKER, color=[0, 0, 0, 0],
                       show=False,
                       tag="chord_play_bar_" + str(idx), parent=canvas_tag)
    dpg.draw_text([8, 10], title,
                  tag="chord_title_" + str(idx),
                  color=title_col, size=24, parent=canvas_tag)
    dpg.draw_text([8, 40], notes,
                  color=COLOR_TEXT_DIM, size=18, parent=canvas_tag)

    # Keybind label in top‑right corner
    if show_keybind and idx < len(KEYBIND_LABELS):
        lbl = KEYBIND_LABELS[idx]
        lbl_w = len(lbl) * 8  # rough width estimate
        dpg.draw_text([CHORD_BOX_W - 8 - lbl_w, 4], lbl,
                      color=COLOR_TEXT_DIM, size=12, parent=canvas_tag)



def draw_prog_cell(canvas_tag: str, cell: ProgCell,
                   idx: int, selected: bool = False,
                   key: str = "C", scale: str = "Major",
                   show_keybind: bool = False):
    """Draw a compact progression grid cell inside *canvas_tag*.

    Shows degree symbol (computed from cell's root vs key/scale),
    chord name, notes, speaker dot, and play bar.
    If *show_keybind* is True, the keyboard shortcut is drawn
    in the top‑right corner.
    """
    dpg.delete_item(canvas_tag, children_only=True)

    # Background and border
    border_col = COLOR_ACCENT if selected else COLOR_CHORD_BORDER
    border_thick = 2 if selected else 1
    dpg.draw_rectangle([0, 0],
                       [PROG_CELL_W - 1, PROG_CELL_H - 1],
                       fill=COLOR_CHORD_BG, color=border_col,
                       thickness=border_thick,
                       tag=f"prog_border_{idx}", parent=canvas_tag)

    # Play bar at bottom
    dpg.draw_rectangle([2, PROG_CELL_H - 6], [PROG_CELL_W - 3, PROG_CELL_H - 2],
                       fill=COLOR_ACTIVE_SPEAKER, color=[0, 0, 0, 0],
                       show=False,
                       tag=f"prog_play_bar_{idx}", parent=canvas_tag)

    # Keybind label in top‑right corner (drawn even on empty cells)
    if show_keybind and idx < len(KEYBIND_LABELS):
        lbl = KEYBIND_LABELS[idx]
        lbl_w = len(lbl) * 7
        dpg.draw_text([PROG_CELL_W - 8 - lbl_w, 3], lbl,
                      color=COLOR_TEXT_DIM, size=10, parent=canvas_tag)

    if cell.is_empty():
        dpg.draw_text([PROG_CELL_W // 2 - 22, PROG_CELL_H // 2 - 8], "Empty",
                      color=COLOR_TEXT_DIM, size=14, parent=canvas_tag)
        return


    # Degree symbol — compute from actual cell root vs key/scale
    from klo_chords.chords import get_degree_for_root
    if cell.root is not None:
        degree = get_degree_for_root(cell.root, key, scale)
    else:
        degree = "?"
    dpg.draw_text([5, 3], degree,
                  tag=f"prog_degree_{idx}",
                  color=COLOR_ACCENT, size=14, parent=canvas_tag)

    # Chord name
    q = quality_symbol(cell.quality).strip()
    name = cell.root + (" " + q if q else "")
    dpg.draw_text([5, 20], name,
                  tag=f"prog_name_{idx}",
                  color=COLOR_TEXT, size=16, parent=canvas_tag)

    # Notes
    notes_str = " ".join(cell.get_notes())
    dpg.draw_text([5, 44], notes_str,
                  color=COLOR_TEXT_DIM, size=13, parent=canvas_tag)



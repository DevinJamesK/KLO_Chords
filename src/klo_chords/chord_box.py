"""
Chord name box drawn on a Dear PyGui drawlist.
Shows root + quality and notes in a compact tile.
Degree is rendered in a separate column to the left.
"""

import dearpygui.dearpygui as dpg
from klo_chords.chords import ChordInfo
from klo_chords.quality import quality_symbol
from klo_chords.theme import (
    COLOR_ACCENT, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_CHORD_BG, COLOR_CHORD_BORDER,
)

CHORD_BOX_W = 154
CHORD_BOX_H = 89


def draw_chord_label(canvas_tag: str, chord: ChordInfo, idx: int,
                     selected: bool = False):
    """Redraw the chord name tile inside *canvas_tag*.
    Degree is shown in a separate column outside this drawlist.
    Selection highlighting is handled externally by state._select_chord()
    via configure_item on the border/title tags.
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
    dpg.draw_text([8, 10], title,
                  tag="chord_title_" + str(idx),
                  color=title_col, size=20, parent=canvas_tag)
    dpg.draw_text([8, 36], notes,
                  color=COLOR_TEXT_DIM, size=16, parent=canvas_tag)

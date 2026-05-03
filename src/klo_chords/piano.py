"""
Piano keyboard rendering on a Dear PyGui drawlist.

Shows one octave (C to B) with highlighted keys.
Chord notes highlight in gold, scale notes in blue.
The bass note (lowest sounding note) highlights in green.
"""

import dearpygui.dearpygui as dpg
from typing import List, Set

# ── Piano key geometry ─────────────────────────────────────────────────────────
_PWW, _PWH = 48, 120   # white key width / height
_PBW, _PBH = 30, 72    # black key width / height
_WHITE_PC = [0, 2, 4, 5, 7, 9, 11]
_BLACK_PC = [1, 3, 6, 8, 10]
_BLACK_X  = [
    _PWW - _PBW // 2,
    2 * _PWW - _PBW // 2,
    4 * _PWW - _PBW // 2,
    5 * _PWW - _PBW // 2,
    6 * _PWW - _PBW // 2,
]
PIANO_CANVAS_W = 7 * _PWW + 2
PIANO_CANVAS_H = _PWH + 4


def build_piano_keys(canvas_tag: str):
    """Draw the static piano key shapes once."""
    for i, pc in enumerate(_WHITE_PC):
        x = i * _PWW
        dpg.draw_rectangle(
            [x, 0], [x + _PWW - 2, _PWH],
            fill=[255, 255, 255, 255], color=[60, 60, 70, 255],
            tag="piano_wkey_" + str(pc), parent=canvas_tag,
        )
    for i, pc in enumerate(_BLACK_PC):
        x = _BLACK_X[i]
        dpg.draw_rectangle(
            [x, 0], [x + _PBW, _PBH],
            fill=[20, 20, 20, 255], color=[0, 0, 0, 0],
            tag="piano_bkey_" + str(pc), parent=canvas_tag,
        )


def update_piano_keys(chord_pcs: Set[int], scale_pcs: Set[int],
                      bass_pc: int = -1):
    """Highlight keys based on chord, scale, and bass note.

    chord_pcs: pitch classes in the chord (gold = chord, blue = scale only)
    bass_pc:   pitch class of the lowest sounding note (green)
    """
    for pc in _WHITE_PC:
        tag = "piano_wkey_" + str(pc)
        if not dpg.does_item_exist(tag):
            continue
        if pc == bass_pc and pc in chord_pcs:
            fill = [80, 230, 80, 255]    # green for bass
        elif pc in chord_pcs:
            fill = [255, 210, 50, 255]   # gold for chord
        elif pc in scale_pcs:
            fill = [100, 180, 255, 255]  # blue for scale only
        else:
            fill = [255, 255, 255, 255]  # white
        dpg.configure_item(tag, fill=fill)

    for pc in _BLACK_PC:
        tag = "piano_bkey_" + str(pc)
        if not dpg.does_item_exist(tag):
            continue
        if pc == bass_pc and pc in chord_pcs:
            fill = [40, 180, 40, 255]     # dark green for bass
        elif pc in chord_pcs:
            fill = [200, 160, 30, 255]   # gold for chord
        elif pc in scale_pcs:
            fill = [40, 80, 180, 255]    # blue for scale only
        else:
            fill = [20, 20, 20, 255]     # black
        dpg.configure_item(tag, fill=fill)

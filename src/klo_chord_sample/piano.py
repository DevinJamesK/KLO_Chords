"""
Piano keyboard rendering on a Dear PyGui drawlist.
"""

import dearpygui.dearpygui as dpg
from typing import Set

from klo_chord_sample.theme import (
    COLOR_ACCENT,
)

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


def update_piano_keys(chord_pcs: Set[int], scale_pcs: Set[int]):
    """Highlight keys based on the selected chord and current scale."""
    for pc in _WHITE_PC:
        tag = "piano_wkey_" + str(pc)
        if not dpg.does_item_exist(tag):
            continue
        if pc in chord_pcs:
            fill = [255, 210, 50, 255]
        elif pc in scale_pcs:
            fill = [100, 180, 255, 255]
        else:
            fill = [255, 255, 255, 255]
        dpg.configure_item(tag, fill=fill)

    for pc in _BLACK_PC:
        tag = "piano_bkey_" + str(pc)
        if not dpg.does_item_exist(tag):
            continue
        if pc in chord_pcs:
            fill = [200, 160, 30, 255]
        elif pc in scale_pcs:
            fill = [40, 80, 180, 255]
        else:
            fill = [20, 20, 20, 255]
        dpg.configure_item(tag, fill=fill)

"""
Fretboard rendering: full-size (detail panel) and mini (chord list preview).

Supports two display modes:
  - "fret":  Shows fret numbers inside the circles (default)
  - "note":  Shows note names inside the circles (root highlighted green)
"""

import dearpygui.dearpygui as dpg
import math
from typing import List, Tuple, Optional

from klo_chords.chords import ChordInfo, get_guitar_diagram, note_to_pc, pc_to_note
from klo_chords.chord_shapes import OPEN_STRING_PCS
from klo_chords.theme import (
    COLOR_BG_LIGHT, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_STRING, COLOR_FRET, COLOR_DOT, COLOR_ROOT_DOT,
    COLOR_MUTED, COLOR_OPEN,
)

# ── Display mode state ──────────────────────────────────────────────────────────
# "fret" = show fret numbers, "note" = show note names (root in green)
_fretboard_mode = "fret"


def set_fretboard_mode(mode: str):
    global _fretboard_mode
    _fretboard_mode = mode


def get_fretboard_mode() -> str:
    return _fretboard_mode


# ── Text centering helper ───────────────────────────────────────────────────────

def _centered_text(x: float, y: float, text: str, size: int, color, parent: str):
    """Draw text centered at (x, y) using the text's approximate width."""
    # Approximate width: ~0.55 * size per character for most fonts
    text_w = len(text) * size * 0.55
    text_h = size * 0.5
    dpg.draw_text(
        [x - text_w / 2, y - text_h],
        text, color=color, size=size, parent=parent,
    )


# ── Mini fretboard (thumbnail in chord list) ──────────────────────────────────

def draw_mini_fretboard(canvas_tag: str, chord: ChordInfo):
    """Draw a small 115x90 fretboard preview inside *canvas_tag*."""
    if not dpg.does_item_exist(canvas_tag):
        return
    dpg.delete_item(canvas_tag, children_only=True)

    W, H = 115, 90
    diagram = get_guitar_diagram(chord)

    if diagram is None:
        dpg.draw_text([W // 2 - 28, H // 2 - 5], "no diagram",
                      color=COLOR_TEXT_DIM, size=14, parent=canvas_tag)
        return

    str_gap = 12                        # tighter spacing for natural proportion
    x0 = (W - 5 * str_gap) // 2         # centered; ~27px → leaves room for fret labels

    y0 = 14
    min_fret = min((f for _, f in diagram if f is not None and f > 0), default=0)
    max_fret = max((f for _, f in diagram if f is not None), default=0)
    has_open  = any(f == 0 for _, f in diagram if f is not None)
    start_fret = 0 if has_open else max(1, min_fret)
    fret_count = min(5, max_fret - start_fret + 2)
    fret_gap = (H - 28) / max(fret_count, 3)

    for f in range(fret_count + 1):
        y = y0 + f * fret_gap
        thickness = 3 if f == 0 else 1
        dpg.draw_line([x0, y], [x0 + 5 * str_gap, y],
                      color=COLOR_FRET, thickness=thickness,
                      parent=canvas_tag)
        if f == 0 and start_fret > 0:
            dpg.draw_text([x0 - 18, y0 - 2],
                          str(start_fret), color=[255, 230, 80, 255], size=16,
                          parent=canvas_tag)

    for s in range(6):
        x = x0 + s * str_gap
        dpg.draw_line([x, y0], [x, y0 + fret_count * fret_gap],
                      color=COLOR_STRING, thickness=1, parent=canvas_tag)

    string_map = {s: None for s in range(6)}
    for s_idx, fret in diagram:
        string_map[s_idx] = fret

    root_pc = note_to_pc(chord.root)
    for s_idx, fret in string_map.items():
        x = x0 + s_idx * str_gap
        if fret is None:
            dpg.draw_text([x - 5, y0 - 10], "X",
                          color=COLOR_MUTED, size=14, parent=canvas_tag)
        elif fret == 0:
            dpg.draw_text([x - 5, y0 - 10], "O",
                          color=COLOR_OPEN, size=14, parent=canvas_tag)
        else:
            dot_y = y0 + (fret - max(start_fret, 1)) * fret_gap
            circle_cy = dot_y + fret_gap / 2
            note_pc = (OPEN_STRING_PCS[s_idx] + fret) % 12
            is_root = (note_pc == root_pc)

            if _fretboard_mode == "note":
                # Show note name, root in green
                dot_color = [60, 210, 100, 255] if is_root else COLOR_DOT
                label = pc_to_note(note_pc)
            else:
                dot_color = COLOR_ROOT_DOT if is_root else COLOR_DOT
                label = str(fret)

            dpg.draw_circle([x, circle_cy], 6,
                            fill=dot_color, color=[0, 0, 0, 0],
                            parent=canvas_tag)
            text_col = [20, 20, 30, 255]
            _centered_text(x, circle_cy, label, 11, text_col, canvas_tag)


# ── Large fretboard (detail panel) ─────────────────────────────────────────────

def draw_fretboard(chord: ChordInfo, voicing_idx: int = 0):
    """Draw the large 360x220 fretboard on the 'fretboard_canvas' drawlist."""
    if not dpg.does_item_exist("fretboard_canvas"):
        return
    dpg.delete_item("fretboard_canvas", children_only=True)

    cw, ch = 360, 220
    diagram = get_guitar_diagram(chord, voicing_idx)

    if diagram is None:
        dpg.draw_text([cw // 2 - 60, ch // 2 - 8], "No diagram available",
                      color=COLOR_TEXT_DIM, size=18, parent="fretboard_canvas")
        return

    string_spacing = cw / 8.5   # 6 strings in ~360px: ~42px apart
    fret_spacing   = ch / 6.5
    x_start = 12                # leftmost string (low E) — circle radius 11 → edge at x=1, no clipping
    y_start = 18

    min_fret  = min(f for _, f in diagram)
    max_fret  = max(f for _, f in diagram)
    has_open  = any(f == 0 for _, f in diagram)
    start_fret = 0 if has_open else max(1, min_fret)
    fret_count = min(5, max_fret - start_fret + 2)

    for f in range(fret_count + 1):
        y = y_start + f * fret_spacing
        thickness = 4 if f == 0 else 1
        dpg.draw_line([x_start, y],
                      [x_start + 5 * string_spacing, y],
                      color=COLOR_FRET, thickness=thickness,
                      parent="fretboard_canvas")
        if f == 0 and start_fret > 0:
            dpg.draw_text([x_start + 5 * string_spacing + 12,
                           y_start + fret_spacing / 3 - 2],
                          str(start_fret), color=[255, 230, 80, 255], size=22,
                          parent="fretboard_canvas")

    for s in range(6):
        x = x_start + s * string_spacing
        dpg.draw_line([x, y_start],
                      [x, y_start + fret_count * fret_spacing],
                      color=COLOR_STRING, thickness=1.5,
                      parent="fretboard_canvas")

    string_map = {s: None for s in range(6)}
    for s_idx, fret in diagram:
        string_map[s_idx] = fret

    root_pc = note_to_pc(chord.root)
    for s_idx, fret in string_map.items():
        x = x_start + s_idx * string_spacing
        if fret is None:
            dpg.draw_text([x - 5, y_start - 18], "X",
                          color=COLOR_MUTED, size=16,
                          parent="fretboard_canvas")
        elif fret == 0:
            dpg.draw_text([x - 5, y_start - 18], "O",
                          color=COLOR_OPEN, size=16,
                          parent="fretboard_canvas")
        else:
            dot_y = y_start + (fret - max(start_fret, 1)) * fret_spacing
            circle_cy = dot_y + fret_spacing / 2
            note_pc = (OPEN_STRING_PCS[s_idx] + fret) % 12
            is_root = (note_pc == root_pc)

            if _fretboard_mode == "note":
                # Show note name, root in green
                dot_color = [60, 210, 100, 255] if is_root else COLOR_DOT
                label = pc_to_note(note_pc)
            else:
                dot_color = COLOR_ROOT_DOT if is_root else COLOR_DOT
                label = str(fret)

            dpg.draw_circle([x, circle_cy], 11,
                            fill=dot_color, color=[0, 0, 0, 0],
                            parent="fretboard_canvas")
            text_col = [20, 20, 30, 255]
            _centered_text(x, circle_cy, label, 18, text_col, "fretboard_canvas")

    for s_idx, sname in enumerate(["E", "A", "D", "G", "B", "e"]):
        x = x_start + s_idx * string_spacing
        dpg.draw_text([x - 4, y_start + fret_count * fret_spacing + 6],
                      sname, color=COLOR_TEXT, size=14,
                      parent="fretboard_canvas")

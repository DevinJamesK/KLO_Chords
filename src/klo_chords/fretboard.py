"""
Fretboard rendering: full-size (detail panel) and mini (chord list preview).
"""

import dearpygui.dearpygui as dpg
from typing import List, Optional, Tuple

from klo_chords.chords import ChordInfo, get_guitar_diagram, note_to_pc
from klo_chords.theme import (
    COLOR_BG_LIGHT, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_STRING, COLOR_FRET, COLOR_DOT, COLOR_ROOT_DOT,
    COLOR_MUTED, COLOR_OPEN,
)

OPEN_STRING_PCS = [4, 9, 2, 7, 11, 4]

# ── Mini fretboard (thumbnail in chord list) ──────────────────────────────────

def draw_mini_fretboard(canvas_tag: str, chord: ChordInfo):
    """Draw a small 95×90 fretboard preview inside *canvas_tag*."""
    if not dpg.does_item_exist(canvas_tag):
        return
    dpg.delete_item(canvas_tag, children_only=True)

    W, H = 95, 90
    diagram = get_guitar_diagram(chord)

    if diagram is None:
        dpg.draw_text([W // 2 - 28, H // 2 - 5], "no diagram",
                      color=COLOR_TEXT_DIM, size=12, parent=canvas_tag)
        return

    x0, y0 = 6, 14
    str_gap = (W - 16) / 5.5

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
            dpg.draw_text([x0 + 5 * str_gap + 2, y0 + 2],
                          str(start_fret), color=COLOR_TEXT_DIM, size=11,
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
            dpg.draw_text([x - 4, y0 - 10], "X",
                          color=COLOR_MUTED, size=12, parent=canvas_tag)
        elif fret == 0:
            dpg.draw_text([x - 4, y0 - 10], "O",
                          color=COLOR_OPEN, size=12, parent=canvas_tag)
        else:
            dot_y = y0 + (fret - start_fret) * fret_gap
            circle_cy = dot_y + fret_gap / 2
            note_pc = (OPEN_STRING_PCS[s_idx] + fret) % 12
            col = COLOR_ROOT_DOT if note_pc == root_pc else COLOR_DOT
            dpg.draw_circle([x, circle_cy], 6,
                            fill=col, color=[0, 0, 0, 0],
                            parent=canvas_tag)
            dpg.draw_text([x - 4, circle_cy - 5],
                          str(fret), color=[20, 20, 30, 255], size=12,
                          parent=canvas_tag)


# ── Large fretboard (detail panel) ─────────────────────────────────────────────

def draw_fretboard(chord: ChordInfo, voicing_idx: int = 0):
    """Draw the large 400×220 fretboard on the 'fretboard_canvas' drawlist."""
    if not dpg.does_item_exist("fretboard_canvas"):
        return
    dpg.delete_item("fretboard_canvas", children_only=True)

    cw, ch = 400, 220
    diagram = get_guitar_diagram(chord, voicing_idx)

    if diagram is None:
        dpg.draw_text([cw // 2 - 60, ch // 2 - 8], "No diagram available",
                      color=COLOR_TEXT_DIM, size=16, parent="fretboard_canvas")
        return

    string_spacing = cw / 9
    fret_spacing   = ch / 6.5
    x_start, y_start = 24, 18

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
            dpg.draw_text([x_start + 5 * string_spacing + 4,
                           y_start + fret_spacing / 3],
                          str(start_fret), color=COLOR_TEXT_DIM, size=16,
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
                          color=COLOR_MUTED, size=14,
                          parent="fretboard_canvas")
        elif fret == 0:
            dpg.draw_text([x - 5, y_start - 18], "O",
                          color=COLOR_OPEN, size=14,
                          parent="fretboard_canvas")
        else:
            dot_y = y_start + (fret - start_fret) * fret_spacing
            circle_cy = dot_y + fret_spacing / 2
            note_pc = (OPEN_STRING_PCS[s_idx] + fret) % 12
            dot_color = COLOR_ROOT_DOT if note_pc == root_pc else COLOR_DOT
            dpg.draw_circle([x, circle_cy], 11,
                            fill=dot_color, color=[0, 0, 0, 0],
                            parent="fretboard_canvas")
            dpg.draw_text([x - 6, circle_cy - 8],
                          str(fret), color=[20, 20, 30, 255], size=18,
                          parent="fretboard_canvas")

    for s_idx, sname in enumerate(["E", "A", "D", "G", "B", "e"]):
        x = x_start + s_idx * string_spacing
        dpg.draw_text([x - 4, y_start + fret_count * fret_spacing + 6],
                      sname, color=COLOR_TEXT, size=12,
                      parent="fretboard_canvas")

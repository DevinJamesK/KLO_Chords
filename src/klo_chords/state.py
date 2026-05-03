"""
Application state and callback functions.

Holds the currently selected key, scale, chord list, etc.
All state mutation goes through callbacks that trigger UI refreshes.
"""

from typing import List, Optional, Set

import dearpygui.dearpygui as dpg

from klo_chords.chords import (
    ChordInfo,
    get_diatonic_chords, get_all_voicings,
    get_scale_notes, note_to_pc,
)
from klo_chords.quality import quality_spelled
from klo_chords.fretboard import draw_fretboard, draw_mini_fretboard
from klo_chords.chord_box import draw_chord_label
from klo_chords.piano import update_piano_keys
from klo_chords.theme import COLOR_ACCENT, COLOR_TEXT, COLOR_CHORD_BORDER

# ── Global state ─────────────────────────────────────────────────────────────────
_current_key          = "C"
_current_scale        = "Major"
_current_chords:      List[ChordInfo] = []
_include_sevenths     = False
_selected_chord_idx:  Optional[int] = None
_current_voicing_idx: int = 0
_current_scale_pcs:   Set[int] = set()
_current_chord_pcs:   Set[int] = set()


def state() -> dict:
    """Return a snapshot of the current state (for introspection)."""
    return dict(
        key=_current_key,
        scale=_current_scale,
        chords=_current_chords,
        sevenths=_include_sevenths,
        selected=_selected_chord_idx,
        voicing=_current_voicing_idx,
        scale_pcs=_current_scale_pcs,
        chord_pcs=_current_chord_pcs,
    )


# ── UI callbacks ─────────────────────────────────────────────────────────────────

def on_key_change(sender, app_data):
    global _current_key, _current_voicing_idx
    _current_key = app_data
    _current_voicing_idx = 0
    _refresh_chords()


def on_scale_change(sender, app_data):
    global _current_scale, _current_voicing_idx
    _current_scale = app_data
    _current_voicing_idx = 0
    _refresh_chords()


def on_sevenths_toggle(sender, app_data):
    global _include_sevenths, _current_voicing_idx
    _include_sevenths = app_data
    _current_voicing_idx = 0
    _refresh_chords()


def on_chord_click(sender, app_data, user_data):
    global _current_voicing_idx
    _current_voicing_idx = 0
    _select_chord(user_data)


def on_next_voicing(sender=None, app_data=None):
    global _current_voicing_idx
    if _selected_chord_idx is None:
        return
    chord = _current_chords[_selected_chord_idx]
    voicings = get_all_voicings(chord)
    if len(voicings) <= 1:
        return
    _current_voicing_idx = (_current_voicing_idx + 1) % len(voicings)
    draw_fretboard(chord, _current_voicing_idx)
    _update_voicing_label(chord)


def on_prev_voicing(sender=None, app_data=None):
    global _current_voicing_idx
    if _selected_chord_idx is None:
        return
    chord = _current_chords[_selected_chord_idx]
    voicings = get_all_voicings(chord)
    if len(voicings) <= 1:
        return
    _current_voicing_idx = (_current_voicing_idx - 1) % len(voicings)
    draw_fretboard(chord, _current_voicing_idx)
    _update_voicing_label(chord)


# ── Internal helpers ──────────────────────────────────────────────────────────────

def _update_voicing_label(chord):
    voicings = get_all_voicings(chord)
    num_v = len(voicings)
    v_idx_display = min(_current_voicing_idx, num_v - 1) if num_v > 0 else 0
    if num_v > 1:
        label = f"  {v_idx_display + 1}/{num_v}  "
    else:
        label = "  1/1  " if num_v == 1 else "  ---  "
    if dpg.does_item_exist("voicing_label"):
        dpg.set_value("voicing_label", label)


def _rebuild_chord_list():
    i = 0
    while dpg.does_item_exist("click_hreg_" + str(i)):
        dpg.delete_item("click_hreg_" + str(i))
        i += 1

    if dpg.does_item_exist("chord_list_group"):
        dpg.delete_item("chord_list_group")

    with dpg.group(parent="chord_list_scroll", tag="chord_list_group"):
        for i, chord in enumerate(_current_chords):
            with dpg.group(horizontal=True, tag="chord_row_" + str(i)):
                dpg.add_spacer(width=4)
                with dpg.drawlist(tag="chord_degree_dl_" + str(i),
                                  width=40, height=90):
                    dpg.draw_text([0, 12], chord.degree,
                                  color=COLOR_ACCENT, size=20)
                with dpg.drawlist(tag="chord_box_" + str(i),
                                  width=155, height=90):
                    pass
                with dpg.drawlist(tag="tab_canvas_" + str(i),
                                  width=95, height=90):
                    pass

            draw_chord_label("chord_box_" + str(i), chord, i)
            draw_mini_fretboard("tab_canvas_" + str(i), chord)

            with dpg.item_handler_registry(tag="click_hreg_" + str(i)):
                dpg.add_item_clicked_handler(callback=on_chord_click,
                                              user_data=i)
            dpg.bind_item_handler_registry("chord_box_" + str(i),
                                            "click_hreg_" + str(i))
            dpg.bind_item_handler_registry("tab_canvas_" + str(i),
                                            "click_hreg_" + str(i))
            dpg.bind_item_handler_registry("chord_degree_dl_" + str(i),
                                            "click_hreg_" + str(i))

    if _current_chords:
        _select_chord(0)


def _select_chord(idx: int):
    global _selected_chord_idx
    _selected_chord_idx = idx
    for i in range(len(_current_chords)):
        selected = (i == idx)
        border = "chord_border_" + str(i)
        title  = "chord_title_"  + str(i)
        if dpg.does_item_exist(border):
            dpg.configure_item(border,
                               color=COLOR_ACCENT if selected
                                      else COLOR_CHORD_BORDER,
                               thickness=2 if selected else 0)
        if dpg.does_item_exist(title):
            dpg.configure_item(title,
                               color=COLOR_ACCENT if selected
                                      else COLOR_TEXT)
    _update_selected_chord()


def _clear_detail():
    for tag in ("detail_root", "detail_quality", "detail_notes",
                "detail_intervals", "voicing_label"):
        if dpg.does_item_exist(tag):
            dpg.set_value(tag, "")
    if dpg.does_item_exist("fretboard_canvas"):
        dpg.delete_item("fretboard_canvas", children_only=True)


def _update_selected_chord():
    global _current_chord_pcs
    if (_selected_chord_idx is None
            or _selected_chord_idx >= len(_current_chords)):
        _clear_detail()
        _current_chord_pcs = set()
        update_piano_keys(_current_chord_pcs, _current_scale_pcs)
        return

    chord = _current_chords[_selected_chord_idx]
    if not dpg.does_item_exist("detail_root"):
        return

    q = quality_spelled(chord.quality)
    dpg.set_value("detail_root",      chord.degree + "  " + chord.root)
    dpg.set_value("detail_quality",   q if q else "Major")
    dpg.set_value("detail_notes",     "  ".join(chord.notes))
    dpg.set_value("detail_intervals", " + ".join(str(x) for x in chord.intervals))

    _update_voicing_label(chord)

    draw_fretboard(chord, _current_voicing_idx)

    _current_chord_pcs = {note_to_pc(n) for n in chord.notes}
    update_piano_keys(_current_chord_pcs, _current_scale_pcs)


def _refresh_chords():
    global _current_chords, _selected_chord_idx, _current_scale_pcs
    _current_chords = get_diatonic_chords(
        _current_key, _current_scale, include_sevenths=_include_sevenths
    )
    _selected_chord_idx = 0 if _current_chords else None

    if dpg.does_item_exist("scale_notes_text"):
        notes = get_scale_notes(_current_key, _current_scale)
        dpg.set_value("scale_notes_text", "  |  ".join(notes))
        _current_scale_pcs = {note_to_pc(n) for n in notes}

    _rebuild_chord_list()

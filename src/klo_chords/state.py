"""
Application state and callback functions.

Holds the currently selected key, scale, chord list, etc.
All state mutation goes through callbacks that trigger UI refreshes.
"""

from __future__ import annotations

import os
from typing import List, Optional, Set

import dearpygui.dearpygui as dpg

import klo_chords.core.prefs as prefs

from klo_chords.core.chords import (
    ChordInfo, ProgCell, NOTE_NAMES, QUALITY_INTERVALS, SCALE_TYPES,
    get_diatonic_chords, get_all_voicings,
    get_scale_notes, note_to_pc, pc_to_note, get_degree_for_root,
    get_accidental_style,
)
from klo_chords.core.quality import quality_spelled, quality_symbol
from klo_chords.rendering.fretboard import draw_fretboard, draw_mini_fretboard
from klo_chords.rendering.chord_box import (
    draw_chord_label, draw_prog_cell,
    PROG_QUALITY_MAP, PROG_QUALITY_REVERSE_MAP, PROG_QUALITY_NAMES,
)
from klo_chords.rendering.piano import (
    update_piano_keys, update_multi_octave_piano, clear_multi_octave_piano,
    build_multi_octave_piano,
    PROG_PIANO_OCTAVES,
)

from klo_chords.audio.sound import (
    play_chord_notes, play_progression_notes, stop_audio, reset_voice_leading,
    set_base_octave, set_playback_mode, set_legato, set_volume,
    set_mute, is_muted,
    set_mode as set_sound_mode,
    is_playing, get_current_midi_notes,
    get_settings as get_sound_settings,
    get_audio_devices, set_device, get_device_name,
)
from klo_chords.rendering.theme import (
    COLOR_ACCENT, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_CHORD_BORDER,
    COLOR_ACTIVE_SPEAKER, COLOR_INACTIVE_SPEAKER,
)

from klo_chords.core.constants import PROG_COLS, PROG_ROWS, PROG_CELLS_TOTAL
from klo_chords.helpers.console_logging import (
    midi_to_note_name as _midi_to_note_name,
    sub_midi as _sub_midi,
    fmt_event as _fmt_event,
    log_progression_row as _log_progression_row,
)


# ── Global state ────────────────────────────────────────────────────────────────
_current_key          = "C"
_current_scale        = "Major"
_current_chords:      List[ChordInfo] = []
_include_sevenths     = False
_selected_chord_idx:  Optional[int] = None
_current_voicing_idx: int = 0
_current_scale_pcs:   Set[int] = set()
_current_chord_pcs:   Set[int] = set()

# ── Progression state ───────────────────────────────────────────────────────────
_prog_key       = "C"
_prog_scale     = "Major"
_prog_sevenths  = True
_prog_cells:    List[ProgCell] = [ProgCell() for _ in range(PROG_CELLS_TOTAL)]
_prog_selected_idx: Optional[int] = None

_current_tab          = "tab_chords"   # shortcut-active tab (never "tab_midi")
_visual_tab           = "tab_chords"   # what's actually shown
_speaker_frame_count  = 0
_prog_sounding_idx: Optional[int] = None

# ── UI display toggles ──────────────────────────────────────────────────────────
_show_keybinds = False
"""Show keyboard shortcut labels on chord cells (toggled via checkbox / Cmd+K)."""



def state() -> dict:
    return dict(
        key=_current_key, scale=_current_scale,
        chords=_current_chords, sevenths=_include_sevenths,
        selected=_selected_chord_idx, voicing=_current_voicing_idx,
        scale_pcs=_current_scale_pcs, chord_pcs=_current_chord_pcs,
    )


# Console logging helpers have been extracted to klo_chords.helpers.console_logging.
# Aliased imports (_midi_to_note_name, _sub_midi, _fmt_event, _log_progression_row) at top of file.


# ── Play helpers ─────────────────────────────────────────────────────────────────

def _play_current_chord():
    if _selected_chord_idx is not None and _selected_chord_idx < len(_current_chords):
        ci = _current_chords[_selected_chord_idx]
        was_playing = is_playing()
        play_chord_notes(ci.notes, root_note=ci.root)
        base_oct = get_sound_settings()["base_octave"]
        from klo_chords.audio.sound import _stack_root_position
        pcs = [note_to_pc(n) for n in ci.notes]
        root_pc = note_to_pc(ci.root)
        midis = _stack_root_position(pcs, base_oct, root_pc)
        midi_names = [_midi_to_note_name(m) for m in midis]
        sub = _sub_midi(root_pc, midis, get_sound_settings())
        sub_name = _midi_to_note_name(sub) if sub is not None else ""
        q = ci.quality if ci.quality != "M" else ""
        tag = f"[chord {_selected_chord_idx:2d}]"
        print(_fmt_event(tag, ci.degree, ci.root + q, f"oct={base_oct}", ci.notes, midi_names, sub_name))
        from klo_chords.audio.midi_engine import send_chord_midi, stop_midi_notes
        if was_playing and not is_playing():
            stop_midi_notes()
        else:
            all_midis = midis + ([sub] if sub is not None else [])
            send_chord_midi(all_midis)


def _play_prog_cell(idx: int, force: bool = False):
    global _prog_sounding_idx
    if 0 <= idx < len(_prog_cells):
        cell = _prog_cells[idx]
        if not cell.is_empty():
            notes = cell.get_notes()
            if notes:
                from klo_chords.audio.sound import _stack_root_position
                if force:
                    from klo_chords.audio.sound import reset_note_history
                    reset_note_history()
                pcs = [note_to_pc(n) for n in notes]
                root_pc = note_to_pc(cell.root)
                eff_oct = cell.effective_octave()
                midis = _stack_root_position(pcs, eff_oct, root_pc)
                midi_names = [_midi_to_note_name(m) for m in midis]
                sub = _sub_midi(root_pc, midis, get_sound_settings())
                sub_name = _midi_to_note_name(sub) if sub is not None else ""
                q = cell.quality if cell.quality != "M" else ""
                degree = get_degree_for_root(cell.root, _prog_key, _prog_scale)
                tag = f"[cell  {idx:2d}]"
                print(_fmt_event(tag, degree, cell.root + q, f"rot={cell.rotation}", notes, midi_names, sub_name))
                was_playing = is_playing()
                play_progression_notes(notes, base_octave=eff_oct, root_pc=root_pc)
                from klo_chords.audio.midi_engine import send_chord_midi, stop_midi_notes
                if was_playing and not is_playing():
                    stop_midi_notes()
                else:
                    all_midis = midis + ([sub] if sub is not None else [])
                    send_chord_midi(all_midis)
                _prog_sounding_idx = idx


# ── Tab switching ────────────────────────────────────────────────────────────────

def on_tab_change(sender, app_data):
    global _current_tab, _visual_tab
    prev_visual = _visual_tab
    _visual_tab = app_data
    if app_data == "tab_midi":
        return
    coming_from_midi = prev_visual == "tab_midi"
    returning_to_same = app_data == _current_tab
    if not (coming_from_midi and returning_to_same):
        stop_audio()
        from klo_chords.audio.midi_engine import stop_midi_notes
        stop_midi_notes()
    _current_tab = app_data


# ── Chord tab callbacks ─────────────────────────────────────────────────────────

def on_key_change(sender, app_data):
    global _current_key, _current_voicing_idx
    _current_key = app_data
    _current_voicing_idx = 0
    _refresh_chords()


def on_scale_change(sender, app_data):
    global _current_scale, _current_voicing_idx, _include_sevenths
    stop_audio()
    _current_scale = app_data
    _current_voicing_idx = 0
    is_heptatonic = len(SCALE_TYPES[app_data].intervals) == 7
    if not is_heptatonic:
        _include_sevenths = False
        dpg.set_value("sevenths_toggle", False)
    dpg.configure_item("sevenths_toggle", enabled=is_heptatonic)
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
    _play_current_chord()


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
    draw_mini_fretboard("tab_canvas_" + str(_selected_chord_idx), chord, _current_voicing_idx)
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
    draw_mini_fretboard("tab_canvas_" + str(_selected_chord_idx), chord, _current_voicing_idx)
    _update_voicing_label(chord)


# ── Progression tab callbacks ───────────────────────────────────────────────────

def on_prog_key_change(sender, app_data):
    global _prog_key
    _prog_key = app_data


def on_prog_scale_change(sender, app_data):
    global _prog_scale, _prog_sevenths
    _prog_scale = app_data
    is_heptatonic = len(SCALE_TYPES[app_data].intervals) == 7
    if not is_heptatonic:
        _prog_sevenths = False
        dpg.set_value("prog_sevenths_toggle", False)
    dpg.configure_item("prog_sevenths_toggle", enabled=is_heptatonic)


def on_prog_sevenths_toggle(sender, app_data):
    global _prog_sevenths
    _prog_sevenths = app_data


def on_prog_fill(sender=None, app_data=None):
    """Fill chords starting from the selected cell, right→down like reading."""
    global _prog_cells
    chords = get_diatonic_chords(
        _prog_key, _prog_scale, include_sevenths=True
    )
    # Start filling from the selected cell, or column 0 row 0 if none selected
    start_idx = _prog_selected_idx if _prog_selected_idx is not None else 0
    for i, chord in enumerate(chords):
        idx = start_idx + i
        if idx >= PROG_CELLS_TOTAL:
            break
        cell = _prog_cells[idx]
        cell.root = chord.root
        cell.quality = chord.quality
        cell.rotation = 0
        cell.voicing_idx = 0
        cell.base_octave = 2
    _rebuild_prog_ui()
    # Auto-select the starting cell so arrow buttons work immediately
    if 0 <= start_idx < PROG_CELLS_TOTAL:
        _select_prog_cell(start_idx)


def on_prog_clear_all(sender=None, app_data=None):
    """Clear all cells in the progression grid."""
    global _prog_cells
    stop_audio()
    for cell in _prog_cells:
        cell.clear()
    _rebuild_prog_ui()
    _select_prog_cell(0)


import platform as _platform
import subprocess as _subprocess
import sys as _sys


def _native_save_path(title: str, default_name: str, ext: str) -> str:
    """Return a save path from the OS-native dialog, or '' if cancelled."""
    if _platform.system() == "Darwin":
        script = (
            f'POSIX path of (choose file name with prompt "{title}"'
            f' default name "{default_name}")'
        )
        r = _subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        path = r.stdout.strip()
        if path and not path.endswith(ext):
            path += ext
        return path
    import tkinter as _tk
    from tkinter import filedialog as _fd
    root = _tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", True)
    path = _fd.asksaveasfilename(
        title=title, defaultextension=ext,
        filetypes=[("KLO Chords", f"*{ext}"), ("All files", "*.*")],
        initialfile=default_name,
    )
    root.destroy()
    return path or ""


def _native_open_path(title: str, ext: str) -> str:
    """Return an open path from the OS-native dialog, or '' if cancelled."""
    if _platform.system() == "Darwin":
        script = f'POSIX path of (choose file with prompt "{title}")'
        r = _subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        return r.stdout.strip()
    import tkinter as _tk
    from tkinter import filedialog as _fd
    root = _tk.Tk()
    root.withdraw()
    root.wm_attributes("-topmost", True)
    path = _fd.askopenfilename(
        title=title,
        filetypes=[("KLO Chords", f"*{ext}"), ("All files", "*.*")],
    )
    root.destroy()
    return path or ""


def on_prog_export(sender=None, app_data=None):
    """Export the progression grid to a .kloc file via native save dialog."""
    import json
    path = _native_save_path("Export Progression", "progression.kloc", ".kloc")
    if not path:
        return
    data = {
        "version": 1,
        "key": _prog_key,
        "scale": _prog_scale,
        "sevenths": _prog_sevenths,
        "cells": [
            {
                "root": cell.root,
                "quality": cell.quality,
                "rotation": cell.rotation,
                "base_octave": cell.base_octave,
                "voicing_idx": cell.voicing_idx,
            }
            for cell in _prog_cells
        ],
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def on_prog_import(sender=None, app_data=None):
    """Import a .kloc progression file via native open dialog."""
    import json
    path = _native_open_path("Import Progression", ".kloc")
    if not path:
        return
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except Exception:
        return
    global _prog_key, _prog_scale, _prog_sevenths
    if "key" in data:
        _prog_key = data["key"]
        if dpg.does_item_exist("prog_key_combo"):
            dpg.set_value("prog_key_combo", _prog_key)
    if "scale" in data:
        _prog_scale = data["scale"]
        if dpg.does_item_exist("prog_scale_combo"):
            dpg.set_value("prog_scale_combo", _prog_scale)
    if "sevenths" in data:
        _prog_sevenths = data["sevenths"]
        if dpg.does_item_exist("prog_sevenths_toggle"):
            dpg.set_value("prog_sevenths_toggle", _prog_sevenths)
    stop_audio()
    for i, cell_data in enumerate(data.get("cells", [])):
        if i >= PROG_CELLS_TOTAL:
            break
        cell = _prog_cells[i]
        cell.root = cell_data.get("root")
        cell.quality = cell_data.get("quality", "M")
        cell.rotation = cell_data.get("rotation", 0)
        cell.base_octave = cell_data.get("base_octave", 3)
        cell.voicing_idx = cell_data.get("voicing_idx", 0)
    _rebuild_prog_ui()
    _select_prog_cell(0)




def on_prog_cell_click(sender, app_data, user_data):
    idx = user_data
    if 0 <= idx < len(_prog_cells):
        from klo_chords.widgets import dpg_keyboard
        shift  = dpg_keyboard.shift_is_down()
        toggle = dpg_keyboard.toggle_is_down()  # Cmd on macOS, Ctrl otherwise
        if shift and toggle:
            # Ctrl/Cmd+Shift+click: add range to existing selection (union)
            on_prog_cell_shift_click(sender, app_data, user_data, union=True)
        elif shift:
            on_prog_cell_shift_click(sender, app_data, user_data)
        elif toggle:
            # Ctrl/Cmd+click: toggle individual cell in/out of multi-select set
            if idx in _prog_selected_set or idx == _get_prog_selected_idx():
                _prog_selected_set.discard(idx)
                if _get_prog_selected_idx() == idx:
                    _clear_prog_selected_idx()
            else:
                _prog_selected_set.add(idx)
            _rebuild_prog_ui()
        else:
            _select_prog_cell(idx)
            _play_prog_cell(idx)


# ── Arrow button callbacks ─────────────────────────────────────────────────────

def on_prog_cell_root_prev(sender=None, app_data=None):
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    else:
        pc = (note_to_pc(cell.root) - 1) % 12
        cell.root = pc_to_note(pc, get_accidental_style(_prog_key))
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx, force=True)


def on_prog_cell_root_next(sender=None, app_data=None):
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    else:
        pc = (note_to_pc(cell.root) + 1) % 12
        cell.root = pc_to_note(pc, get_accidental_style(_prog_key))
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx, force=True)


def on_prog_cell_quality_prev(sender=None, app_data=None):
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    else:
        current_display = PROG_QUALITY_REVERSE_MAP.get(cell.quality, "Major")
        idx = PROG_QUALITY_NAMES.index(current_display) if current_display in PROG_QUALITY_NAMES else 0
        new_display = PROG_QUALITY_NAMES[(idx - 1) % len(PROG_QUALITY_NAMES)]
        cell.quality = PROG_QUALITY_MAP.get(new_display, "M")
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx, force=True)


def on_prog_cell_quality_next(sender=None, app_data=None):
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    else:
        current_display = PROG_QUALITY_REVERSE_MAP.get(cell.quality, "Major")
        idx = PROG_QUALITY_NAMES.index(current_display) if current_display in PROG_QUALITY_NAMES else 0
        new_display = PROG_QUALITY_NAMES[(idx + 1) % len(PROG_QUALITY_NAMES)]
        cell.quality = PROG_QUALITY_MAP.get(new_display, "M")
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx, force=True)


def _cell_in_midi_range(cell: ProgCell) -> bool:
    """Return True if every MIDI note for *cell* is in the valid 0-127 range."""
    notes = cell.get_notes()
    if not notes:
        return True
    from klo_chords.audio.sound import _stack_root_position
    pcs = [note_to_pc(n) for n in notes]
    root_pc = note_to_pc(cell.root) if cell.root else 0
    midi_notes = _stack_root_position(pcs, cell.effective_octave(), root_pc)
    return all(0 <= m <= 127 for m in midi_notes)


def on_prog_cell_inversion_prev(sender=None, app_data=None):
    """Move the chord down the keyboard (previous inversion / rotation step)."""
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    cell.rotation -= 1
    if not _cell_in_midi_range(cell):
        cell.rotation += 1  # revert — would go out of MIDI range
        return
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx, force=True)


def on_prog_cell_inversion_next(sender=None, app_data=None):
    """Move the chord up the keyboard (next inversion / rotation step)."""
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    cell.rotation += 1
    if not _cell_in_midi_range(cell):
        cell.rotation -= 1  # revert — would go out of MIDI range
        return
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx, force=True)


def on_prog_cell_octave_prev(sender=None, app_data=None):
    """Lower the base octave of the selected cell."""
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    cell.base_octave = max(0, cell.base_octave - 1)
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx, force=True)


def on_prog_cell_octave_next(sender=None, app_data=None):
    """Raise the base octave of the selected cell."""
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    cell.base_octave = min(8, cell.base_octave + 1)
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx, force=True)


# ── Arrow key callback (progression tab) ─────────────────────────────────────────

def on_prog_cell_arrow_press(sender, app_data, user_data):
    """Arrow keys for the progression tab: Left/Right = inversion (Shift = root), Up/Down = quality."""
    global _current_tab
    if _current_tab != "tab_progression":
        return
    if _prog_selected_idx is None:
        return
    from klo_chords.widgets import dpg_keyboard
    action = str(user_data)
    if action == "inv_prev":
        if dpg_keyboard.shift_is_down():
            on_prog_cell_root_prev()
        else:
            on_prog_cell_inversion_prev()
    elif action == "inv_next":
        if dpg_keyboard.shift_is_down():
            on_prog_cell_root_next()
        else:
            on_prog_cell_inversion_next()
    elif action == "quality_prev":
        on_prog_cell_quality_prev()
    elif action == "quality_next":
        on_prog_cell_quality_next()


# ── Degree helper ────────────────────────────────────────────────────────────────

def _get_degree_for_col(col: int) -> str:
    degrees = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
    return degrees[col] if 0 <= col < len(degrees) else '?'


# ── Keyboard callback ────────────────────────────────────────────────────────────

def on_key_press(sender, app_data, user_data):
    global _current_tab
    from klo_chords.widgets import dpg_keyboard
    # Alt+key: play/select suggestion cards
    # Shift+Alt → range select, Cmd/Ctrl+Alt → single toggle, Alt alone → play
    if dpg_keyboard.alt_is_down():
        if _current_tab == "tab_progression" and dpg.does_item_exist("suggestion_panel"):
            card_idx = user_data
            available_cats, cat_groups = _get_sugg_cat_groups(_sugg_last_suggestions)
            if available_cats:
                global _sugg_playing_card_idx, _sugg_selected_set, _sugg_selection_anchor
                if card_idx == _SUGG_ORIG_CARD_IDX:
                    orig_suggs = [s for s in _sugg_last_suggestions if s.category == "original"]
                    if orig_suggs:
                        s = orig_suggs[0]
                        if dpg_keyboard.shift_is_down():
                            _sugg_range_select(_SUGG_ORIG_CARD_IDX)
                        elif dpg_keyboard.toggle_is_down():
                            _toggle_suggestion_selection(_SUGG_ORIG_CARD_IDX)
                        else:
                            if _sugg_playing_card_idx == _SUGG_ORIG_CARD_IDX and is_playing():
                                stop_audio()
                                from klo_chords.audio.midi_engine import stop_midi_notes
                                stop_midi_notes()
                                _sugg_playing_card_idx = None
                            else:
                                _sugg_selected_set = {_SUGG_ORIG_CARD_IDX}
                                _sugg_selection_anchor = _SUGG_ORIG_CARD_IDX
                                _sugg_playing_card_idx = _SUGG_ORIG_CARD_IDX
                                _apply_suggestion(s)
                                _rebuild_sugg_selection_highlights()
                else:
                    visible = cat_groups.get(available_cats[_sugg_current_cat_idx], [])
                    if 0 <= card_idx < len(visible):
                        if dpg_keyboard.shift_is_down():
                            _sugg_range_select(card_idx)
                        elif dpg_keyboard.toggle_is_down():
                            _toggle_suggestion_selection(card_idx)
                        else:
                            if card_idx == _sugg_playing_card_idx and is_playing():
                                stop_audio()
                                from klo_chords.audio.midi_engine import stop_midi_notes
                                stop_midi_notes()
                                _sugg_playing_card_idx = None
                            else:
                                _sugg_selected_set = {card_idx}
                                _sugg_selection_anchor = card_idx
                                _sugg_playing_card_idx = card_idx
                                _apply_suggestion(visible[card_idx])
                                _rebuild_sugg_selection_highlights()
        return
    # Don't fire if platform-native modifier is held (conflicts with shortcuts)
    if dpg_keyboard.toggle_is_down():
        return
    if _current_tab == "tab_chords":
        idx = user_data
        if 0 <= idx < len(_current_chords):
            global _current_voicing_idx
            _current_voicing_idx = 0
            _select_chord(idx)
            _play_current_chord()
    elif _current_tab == "tab_progression":
        idx = user_data
        if idx < PROG_CELLS_TOTAL and idx < len(_prog_cells):
            if dpg_keyboard.shift_is_down():
                if idx in _prog_selected_set or idx == _get_prog_selected_idx():
                    _prog_selected_set.discard(idx)
                    if _get_prog_selected_idx() == idx:
                        _clear_prog_selected_idx()
                else:
                    _prog_selected_set.add(idx)
                _rebuild_prog_ui()
            else:
                _select_prog_cell(idx)
                _play_prog_cell(idx)


# ── Sound setting callbacks ──────────────────────────────────────────────────────

# ── Preferences persistence helper ───────────────────────────────────────────

def _save_prefs():
    """Collect current sound/UI state and persist to preferences.json."""
    s = get_sound_settings()
    from klo_chords.rendering.fretboard import get_fretboard_mode
    prefs.save({
        "sound_enabled":   s.get("enabled", True),
        "volume":          int(round(s.get("volume", 0.75) * 100)),
        "wave":            s.get("mode", "triangle"),
        "audio_quality":   s.get("audio_quality", "smooth"),
        "legato":          s.get("legato", True),
        "playback_mode":   s.get("playback_mode", "toggle"),
        "random_velocity": s.get("random_vel", True),
        "vel_min":         s.get("vel_min", 60),
        "vel_max":         s.get("vel_max", 100),
        "base_octave":     s.get("base_octave", 3),
        "show_note_names": get_fretboard_mode() == "note",
        "show_keybinds":   _show_keybinds,
        "sub_oscillator":  s.get("sub_oscillator", False),
        "audio_device":    get_device_name(),
    })


def on_sound_enable_toggle(sender, app_data):
    from klo_chords.audio.sound import set_enabled
    set_enabled(app_data)
    _save_prefs()


def on_wave_type_change(sender, app_data):
    """app_data may be display name (Triangle) or internal name (triangle)."""
    internal = app_data.lower() if app_data in ("Triangle", "Sine", "Sawtooth") else app_data
    set_sound_mode(internal)
    # Update both combos if they exist
    from klo_chords.rendering.theme import WAVE_INTERNAL_TO_DISPLAY
    display = WAVE_INTERNAL_TO_DISPLAY.get(internal, "Triangle")
    if dpg.does_item_exist("sound_mode_combo"):
        dpg.set_value("sound_mode_combo", display)
    if dpg.does_item_exist("toolbar_wave_combo"):
        dpg.set_value("toolbar_wave_combo", display)
    # Redraw wave preview
    from klo_chords.gui import _draw_wave_preview
    _draw_wave_preview(internal)
    _save_prefs()


def on_audio_quality_change(sender, app_data):
    """Handle Audio Quality combo change. app_data is 'Smooth', 'Responsive', or 'Legacy'."""
    quality_map = {"Smooth": "smooth", "Responsive": "responsive", "Legacy": "legacy"}
    internal = quality_map.get(app_data, "smooth")
    from klo_chords.audio.sound import set_audio_quality
    set_audio_quality(internal)
    _save_prefs()


def on_audio_device_change(sender, app_data):
    """Handle Audio Device combo change. app_data is the device name string."""
    if app_data == "System Default":
        set_device(None)
    else:
        devices = get_audio_devices()
        for dev in devices:
            if dev["name"] == app_data:
                set_device(dev["index"])
                break
    _save_prefs()


def on_random_velocity_toggle(sender, app_data):
    from klo_chords.audio.sound import set_random_velocity
    set_random_velocity(app_data)
    _save_prefs()


def on_vel_min_change(sender, app_data):
    from klo_chords.audio.sound import set_velocity_range
    set_velocity_range(app_data, _get_vel_max())
    _save_prefs()


def on_vel_max_change(sender, app_data):
    from klo_chords.audio.sound import set_velocity_range
    set_velocity_range(_get_vel_min(), app_data)
    _save_prefs()


def on_base_octave_change(sender, app_data):
    set_base_octave(app_data)
    _save_prefs()


def on_playback_mode_change(sender, app_data):
    mode_map = {"Toggle/Latch": "toggle", "One-Shot": "oneshot"}
    set_playback_mode(mode_map.get(app_data, "toggle"))
    reset_voice_leading()
    _save_prefs()


def on_legato_toggle(sender, app_data):
    set_legato(app_data)
    if dpg.does_item_exist("toolbar_legato_toggle"):
        dpg.set_value("toolbar_legato_toggle", app_data)
    if dpg.does_item_exist("sound_legato_toggle"):
        dpg.set_value("sound_legato_toggle", app_data)
    _save_prefs()


def on_sub_oscillator_toggle(sender, app_data):
    from klo_chords.audio.sound import set_sub_oscillator
    set_sub_oscillator(app_data)
    _save_prefs()


def on_reset_prefs(sender=None, app_data=None):
    path = prefs.get_path()
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
    d = prefs.DEFAULTS
    from klo_chords.audio.sound import (
        set_volume, set_enabled, set_mode, set_audio_quality,
        set_legato, set_playback_mode, set_random_velocity,
        set_velocity_range, set_base_octave, set_sub_oscillator,
    )
    set_volume(d["volume"] / 100.0)
    set_enabled(d["sound_enabled"])
    set_mode(d["wave"])
    set_audio_quality(d["audio_quality"])
    set_legato(d["legato"])
    set_playback_mode(d["playback_mode"])
    set_random_velocity(d["random_velocity"])
    set_velocity_range(d["vel_min"], d["vel_max"])
    set_base_octave(d["base_octave"])
    set_sub_oscillator(d["sub_oscillator"])

    wave_display = {"triangle": "Triangle", "sine": "Sine", "sawtooth": "Sawtooth"}
    quality_display = {"smooth": "Smooth", "responsive": "Responsive", "legacy": "Legacy"}
    playback_display = {"toggle": "Toggle/Latch", "oneshot": "One-Shot"}

    for tag, val in [
        ("volume_slider",        d["volume"]),
        ("sound_enable",         d["sound_enabled"]),
        ("random_vel",           d["random_velocity"]),
        ("vel_min_slider",       d["vel_min"]),
        ("vel_max_slider",       d["vel_max"]),
        ("base_octave_slider",   d["base_octave"]),
        ("sound_legato_toggle",  d["legato"]),
        ("toolbar_legato_toggle", d["legato"]),
        ("toolbar_sub_osc_toggle", d["sub_oscillator"]),
        ("toolbar_show_keybinds", d["show_keybinds"]),
        ("fretboard_mode_toggle", d["show_note_names"]),
        ("sound_mode_combo",     wave_display.get(d["wave"], "Triangle")),
        ("toolbar_wave_combo",   wave_display.get(d["wave"], "Triangle")),
        ("sound_quality_combo",  quality_display.get(d["audio_quality"], "Legacy")),
        ("playback_mode_combo",  playback_display.get(d["playback_mode"], "Toggle/Latch")),
    ]:
        if dpg.does_item_exist(tag):
            dpg.set_value(tag, val)

    global _show_keybinds
    _show_keybinds = d["show_keybinds"]

    from klo_chords.rendering.fretboard import set_fretboard_mode
    set_fretboard_mode("note" if d["show_note_names"] else "fret")

    _rebuild_chord_ui()


def on_volume_change(sender, app_data):
    """Volume slider changed. app_data is 0-100 percentage."""
    # Convert percentage (0-100) to internal 0.0-1.0
    set_volume(app_data / 100.0)
    # Update slider color based on mute state
    if dpg.does_item_exist("volume_slider"):
        if app_data <= 0:
            dpg.configure_item("volume_slider", default_value=0)
        # Update the mute theme
        if is_muted() and app_data > 0:
            # Unmute was triggered by slider movement
            set_mute(False)
            _update_volume_theme(False)
    _save_prefs()


def on_mute_toggle(sender=None, app_data=None):
    """Toggle mute on/off. ESC key triggers this."""
    currently_muted = is_muted()
    set_mute(not currently_muted)
    if dpg.does_item_exist("volume_slider"):
        if is_muted():
            dpg.set_value("volume_slider", 0)
        else:
            # Restore to stored volume percentage
            from klo_chords.audio.sound import get_settings
            vol = get_settings()["volume"]
            dpg.set_value("volume_slider", int(round(vol * 100)))
    _update_volume_theme(is_muted())


def on_fretboard_mode_change(sender, app_data):
    """Toggle fretboard between fret numbers and note names."""
    from klo_chords.rendering.fretboard import set_fretboard_mode, get_fretboard_mode
    mode = get_fretboard_mode()
    new_mode = "note" if mode == "fret" else "fret"
    set_fretboard_mode(new_mode)
    if _selected_chord_idx is not None and _selected_chord_idx < len(_current_chords):
        chord = _current_chords[_selected_chord_idx]
        draw_fretboard(chord, _current_voicing_idx)
    _rebuild_chord_ui()
    _save_prefs()


def on_keybinds_toggle(sender=None, app_data=None):
    """Toggle the display of keybind labels on chord cells."""
    global _show_keybinds
    if app_data is not None:
        _show_keybinds = bool(app_data)
    else:
        _show_keybinds = not _show_keybinds
    # Sync the checkbox in the toolbar
    if dpg.does_item_exist("toolbar_show_keybinds"):
        dpg.set_value("toolbar_show_keybinds", _show_keybinds)
    _rebuild_chord_ui()
    _rebuild_prog_ui()
    if dpg.does_item_exist("suggestion_panel") and _sugg_last_suggestions:
        dpg.delete_item("suggestion_panel", children_only=True)
        _build_suggestion_cards(_sugg_last_suggestions, cat_idx=_sugg_current_cat_idx)
        _rebuild_sugg_selection_highlights()
    _save_prefs()


def get_show_keybinds() -> bool:
    """Return whether keybind labels should be displayed on cells."""
    return _show_keybinds


def init_show_keybinds(val: bool):
    """Set keybinds state from saved prefs before DPG context exists."""
    global _show_keybinds
    _show_keybinds = val



def on_stop(sender=None, app_data=None):
    """Stop any currently playing chord (spacebar handler)."""
    stop_audio()
    from klo_chords.audio.midi_engine import stop_midi_notes
    stop_midi_notes()


def _update_volume_theme(muted: bool):
    """Update the volume slider theme to red when muted."""
    if not dpg.does_item_exist("volume_slider"):
        return
    if muted:
        with dpg.theme() as mute_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [80, 20, 20, 255])
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, [200, 40, 40, 255])
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, [255, 60, 60, 255])
        dpg.bind_item_theme("volume_slider", mute_theme)
    else:
        dpg.bind_item_theme("volume_slider", None)


def _get_vel_min() -> int:
    return get_sound_settings()["vel_min"]


def _get_vel_max() -> int:
    return get_sound_settings()["vel_max"]


# ── Internal helpers ──────────────────────────────────────────────────────────────

def _update_voicing_label(chord):
    voicings = get_all_voicings(chord)
    num_v = len(voicings)
    v_idx_display = min(_current_voicing_idx, num_v - 1) if num_v > 0 else 0
    if num_v > 1:
        label = f"  {v_idx_display + 1}/{num_v}"
    else:
        label = "  1/1" if num_v == 1 else "  ---"
    # Pad to constant width so layout doesn't shift (e.g. "1/3" vs "1/10")
    label = label.ljust(8)
    if dpg.does_item_exist("voicing_label"):
        dpg.set_value("voicing_label", label)


def _get_inversion_name(root_pc: int, bass_pc: int) -> str:
    for offset, name in [
        (0, "Root Position"), (3, "1st Inversion"), (4, "1st Inversion"),
        (7, "2nd Inversion"), (10, "3rd Inversion"), (11, "3rd Inversion"),
    ]:
        if bass_pc == (root_pc + offset) % 12:
            return name
    return "?"


def _update_inversion_display():
    midi_notes = get_current_midi_notes() if is_playing() else []
    if not midi_notes or not dpg.does_item_exist("detail_inversion"):
        if dpg.does_item_exist("detail_inversion"):
            dpg.set_value("detail_inversion", "")
        if dpg.does_item_exist("detail_sounding_notes"):
            dpg.set_value("detail_sounding_notes", "")
        return

    note_names = [_midi_to_note_name(m) for m in midi_notes]
    chord = _current_chords[_selected_chord_idx] if (_selected_chord_idx is not None and _selected_chord_idx < len(_current_chords)) else None
    if chord:
        root_pc = note_to_pc(chord.root)
        sub_on = get_sound_settings().get("sub_oscillator", False)
        chord_notes = midi_notes[1:] if sub_on and len(midi_notes) > 1 else midi_notes
        bass_pc = chord_notes[0] % 12 if chord_notes else root_pc
        inv_name = _get_inversion_name(root_pc, bass_pc)
        notes_str = "  ".join(note_names)
        dpg.set_value("detail_inversion", f"{inv_name}  ({notes_str})")
        dpg.set_value("detail_sounding_notes", "")
    else:
        dpg.set_value("detail_inversion", "")
        dpg.set_value("detail_sounding_notes", "")


def _rebuild_chord_ui():
    i = 0
    while dpg.does_item_exist("click_hreg_" + str(i)):
        dpg.delete_item("click_hreg_" + str(i))
        i += 1

    if dpg.does_item_exist("chord_list_group"):
        dpg.delete_item("chord_list_group")

    with dpg.group(parent="chord_list_scroll", tag="chord_list_group"):
        if not _current_chords:
            dpg.add_spacer(height=16)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=60)
                with dpg.group():
                    dpg.add_text("Pentatonic and blues scales don't have\ndiatonic chords.",
                                 color=COLOR_TEXT_DIM)
                    dpg.add_spacer(height=8)
                    dpg.add_text("Use the Progression tab to build\nchord progressions manually.",
                                 color=COLOR_TEXT_DIM)
            dpg.add_spacer(height=554)
        for i, chord in enumerate(_current_chords):
            with dpg.group(horizontal=True, tag="chord_row_" + str(i)):
                dpg.add_spacer(width=6)
                with dpg.drawlist(tag="chord_degree_dl_" + str(i),
                                  width=40, height=90):
                    dpg.draw_text([0, 8], chord.degree,
                                  color=COLOR_ACCENT, size=18)
                dpg.add_spacer(width=6)
                with dpg.drawlist(tag="chord_box_" + str(i),
                                  width=140, height=90):
                    pass
                dpg.add_spacer(width=6)
                with dpg.drawlist(tag="tab_canvas_" + str(i),
                                  width=115, height=90):
                    pass

            draw_chord_label("chord_box_" + str(i), chord, i, show_keybind=_show_keybinds)
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
        restore_idx = _selected_chord_idx if _selected_chord_idx is not None and _selected_chord_idx < len(_current_chords) else 0
        _select_chord(restore_idx)
    else:
        _update_selected_chord()


def _refresh_prog_cell(idx: int):
    tag = f"prog_cell_{idx}"
    if dpg.does_item_exist(tag):
        cell = _prog_cells[idx] if idx < len(_prog_cells) else ProgCell()
        # A cell is highlighted if it's the primary selection OR in the multi-select set
        selected = (idx == _prog_selected_idx) or (idx in _prog_selected_set)
        draw_prog_cell(tag, cell, idx, selected=selected,
                       key=_prog_key, scale=_prog_scale,
                       show_keybind=_show_keybinds)



def _update_prog_piano(cell: ProgCell):
    """Update the multi-octave piano with root-position voicing matching play_progression_notes.

    Uses the same _stack_root_position logic as sound.py so display matches audio.
    The octave display shows the effective octave (base_octave + wrap shift).
    """
    notes = cell.get_notes()
    if not notes:
        clear_multi_octave_piano("prog_piano_canvas", start_octave=3)
        if dpg.does_item_exist("prog_detail_inv_name"):
            dpg.set_value("prog_detail_inv_name", "")
        return

    from klo_chords.audio.sound import _stack_root_position

    eff_oct = cell.effective_octave()
    pcs = [note_to_pc(n) for n in notes]
    root_pc = note_to_pc(cell.root) if cell.root else 0
    midi_notes = _stack_root_position(pcs, eff_oct, root_pc)

    # When sub-oscillator is on and this cell is sounding, the lowest live note
    # is the root copy below the chord. Strip it (index 0 of sorted live notes)
    # so the inversion name reflects the chord, not the sub — same pattern as
    # _update_inversion_display in the Chords tab.
    sub_on = get_sound_settings().get("sub_oscillator", False)
    if sub_on and is_playing() and _prog_sounding_idx == _prog_selected_idx:
        live = get_current_midi_notes()
        chord_midi = live[1:] if live and len(live) > 1 else (live or midi_notes)
    else:
        chord_midi = midi_notes

    # Always use _stack_root_position output for inversion — live notes carry
    # the sub bass note and may still reflect the previous chord at call time.
    bass_midi = midi_notes[0] if midi_notes else -1

    # Display octave always matches the effective octave.
    if dpg.does_item_exist("prog_detail_octave"):
        dpg.configure_item("prog_detail_octave", label=str(eff_oct))

    # Calculate the octave range so all notes fit in the 2-octave display
    if midi_notes:
        start_octave = (min(midi_notes) // 12) + 1
    else:
        start_octave = 3

    if dpg.does_item_exist("prog_piano_canvas"):
        dpg.delete_item("prog_piano_canvas", children_only=True)
        build_multi_octave_piano("prog_piano_canvas", start_octave=start_octave)

    update_multi_octave_piano("prog_piano_canvas", midi_notes, bass_midi,
                              start_octave=start_octave)

    inv_name = _get_inversion_name(root_pc, bass_midi % 12)
    if dpg.does_item_exist("prog_detail_inv_name"):
        notes_str = "  ".join(_midi_to_note_name(m) for m in midi_notes)
        dpg.set_value("prog_detail_inv_name", f"{inv_name}  ({notes_str})")



def _update_prog_detail(idx: int):
    if not dpg.does_item_exist("prog_detail_pos"):
        return
    cell = _prog_cells[idx] if idx < len(_prog_cells) else ProgCell()
    row = idx // PROG_COLS + 1
    col = idx % PROG_COLS + 1
    from klo_chords.core.chords import get_degree_for_root
    real_degree = get_degree_for_root(cell.root, _prog_key, _prog_scale) if cell.root and not cell.is_empty() else "?"
    dpg.set_value("prog_detail_pos", f"R{row}, C{col} ({real_degree})")

    if cell.is_empty():
        dpg.configure_item("prog_detail_root", label="C")
        dpg.configure_item("prog_detail_quality", label="Major")
        dpg.configure_item("prog_detail_inversion", label="Root")
        dpg.configure_item("prog_detail_notes", label="--")
        if dpg.does_item_exist("prog_detail_octave"):
            dpg.configure_item("prog_detail_octave", label="3")
        clear_multi_octave_piano("prog_piano_canvas")
        if dpg.does_item_exist("prog_detail_inv_name"):
            dpg.set_value("prog_detail_inv_name", "")
    else:
        dpg.configure_item("prog_detail_root", label=cell.root)
        display_q = PROG_QUALITY_REVERSE_MAP.get(cell.quality, "Major")
        dpg.configure_item("prog_detail_quality", label=display_q)
        inv_labels = {0: "Root", 1: "1st", 2: "2nd", 3: "3rd"}
        intervals = QUALITY_INTERVALS.get(cell.quality, [0, 4, 7])
        inv_idx = cell.rotation % max(1, len(intervals))
        inv_name = inv_labels.get(inv_idx, "Root")
        dpg.configure_item("prog_detail_inversion", label=inv_name)
        notes_str = " ".join(cell.get_notes()) if cell.get_notes() else "--"
        dpg.configure_item("prog_detail_notes", label=notes_str)
        # Octave display is set by _update_prog_piano below (effective octave from root MIDI).
        _update_prog_piano(cell)


def _rebuild_prog_ui():
    for idx in range(PROG_CELLS_TOTAL):
        _refresh_prog_cell(idx)
    if _prog_selected_idx is not None and _prog_selected_idx < len(_prog_cells):
        _update_prog_detail(_prog_selected_idx)


def _select_prog_cell(idx: int):
    global _prog_selected_idx
    # Clear multi-selection on normal (non-shift) click
    _prog_selected_set.clear()
    _prog_selected_idx = idx
    _rebuild_prog_ui()
    _update_prog_detail(idx)
    _refresh_suggestion_panel()


def _get_prog_selected_idx():
    """Return the current primary selected cell index, or None."""
    return _prog_selected_idx


def _clear_prog_selected_idx():
    """Set the primary selected cell index to None."""
    global _prog_selected_idx
    _prog_selected_idx = None


# ── Chord tab detail ─────────────────────────────────────────────────────────────

def _select_chord(idx: int):
    global _selected_chord_idx
    _selected_chord_idx = idx
    for i in range(len(_current_chords)):
        selected = (i == idx)
        border = "chord_border_" + str(i)
        title  = "chord_title_"  + str(i)
        if dpg.does_item_exist(border):
            dpg.configure_item(border,
                               color=COLOR_ACCENT if selected else COLOR_CHORD_BORDER,
                               thickness=2 if selected else 0)
        if dpg.does_item_exist(title):
            dpg.configure_item(title,
                               color=COLOR_ACCENT if selected else COLOR_TEXT)
    _update_selected_chord()


def _clear_detail():
    for tag in ("detail_root", "detail_quality", "detail_notes",
                "detail_intervals", "voicing_label",
                "detail_inversion", "detail_sounding_notes"):
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
    update_piano_keys(_current_chord_pcs, _current_scale_pcs, bass_pc=-1)


def _refresh_chords():
    global _current_chords, _selected_chord_idx, _current_scale_pcs
    scale = SCALE_TYPES.get(_current_scale)
    if scale and len(scale.intervals) == 7:
        _current_chords = get_diatonic_chords(
            _current_key, _current_scale, include_sevenths=_include_sevenths
        )
    else:
        _current_chords = []
    _selected_chord_idx = 0 if _current_chords else None

    if dpg.does_item_exist("scale_notes_text"):
        notes = get_scale_notes(_current_key, _current_scale)
        dpg.set_value("scale_notes_text", "  |  ".join(notes))
        _current_scale_pcs = {note_to_pc(n) for n in notes}

    reset_voice_leading()
    _rebuild_chord_ui()


def _refresh_progression():
    global _prog_key, _prog_scale, _prog_cells
    if dpg.does_item_exist("prog_key_combo"):
        _prog_key = dpg.get_value("prog_key_combo")
    if dpg.does_item_exist("prog_scale_combo"):
        _prog_scale = dpg.get_value("prog_scale_combo")
    chords = get_diatonic_chords(
        _prog_key, _prog_scale, include_sevenths=True
    )
    for i in range(PROG_COLS):
        if i < len(chords):
            cell = _prog_cells[i]
            cell.root = chords[i].root
            cell.quality = chords[i].quality
            cell.rotation = 0
            cell.voicing_idx = 0
            cell.base_octave = 2
        else:
            _prog_cells[i].clear()
    for i in range(PROG_COLS, PROG_CELLS_TOTAL):
        if _prog_cells[i].root is not None:
            _prog_cells[i].clear()
    _rebuild_prog_ui()
    _log_progression_row(0, _prog_cells, PROG_COLS)
    # Auto-select the first cell so arrow buttons work immediately
    if _prog_cells and not _prog_cells[0].is_empty():
        _select_prog_cell(0)


def _refresh_speaker_indicators():
    global _speaker_frame_count, _prog_sounding_idx
    _speaker_frame_count += 1
    playing = is_playing()

    for i in range(len(_current_chords)):
        is_sounding = playing and _selected_chord_idx == i
        bar_tag = "chord_play_bar_" + str(i)
        if dpg.does_item_exist(bar_tag):
            try:
                dpg.configure_item(bar_tag, show=is_sounding)
            except (SystemError, RuntimeError):
                pass  # DPG item may have been destroyed

    for i in range(PROG_CELLS_TOTAL):
        is_sounding = playing and _prog_sounding_idx == i
        bar_tag = "prog_play_bar_" + str(i)
        if dpg.does_item_exist(bar_tag):
            try:
                dpg.configure_item(bar_tag, show=is_sounding)
            except (SystemError, RuntimeError):
                pass  # DPG item may have been destroyed

    sugg_playing = (playing
                    and _prog_sounding_idx == _prog_selected_idx
                    and _sugg_playing_card_idx is not None)
    for i in range(_sugg_card_count):
        bar_tag = f"prog_play_bar_{_SUGG_IDX_BASE + i}"
        if dpg.does_item_exist(bar_tag):
            try:
                dpg.configure_item(bar_tag, show=(sugg_playing and i == _sugg_playing_card_idx))
            except (SystemError, RuntimeError):
                pass  # DPG item may have been destroyed
    _orig_sugg = next((s for s in _sugg_last_suggestions if s.category == "original"), None)
    _cell_is_original = (
        _orig_sugg is not None
        and _prog_selected_idx is not None
        and not _prog_cells[_prog_selected_idx].is_empty()
        and _prog_cells[_prog_selected_idx].root == _orig_sugg.root
        and _prog_cells[_prog_selected_idx].quality == _orig_sugg.quality
    )
    orig_bar_active = (playing
                       and _prog_sounding_idx == _prog_selected_idx
                       and (_cell_is_original
                            or _sugg_playing_card_idx == _SUGG_ORIG_CARD_IDX))
    for j in range(_sugg_orig_card_count):
        bar_tag = f"prog_play_bar_{_SUGG_IDX_BASE + _SUGG_ORIG_IDX_BASE + j}"
        if dpg.does_item_exist(bar_tag):
            try:
                dpg.configure_item(bar_tag, show=orig_bar_active)
            except (SystemError, RuntimeError):
                pass  # DPG item may have been destroyed

    if not playing:
        _prog_sounding_idx = None

    _update_inversion_display()
    if playing and _selected_chord_idx is not None and _selected_chord_idx < len(_current_chords):
        midi_notes = get_current_midi_notes()
        if midi_notes:
            sub_on = get_sound_settings().get("sub_oscillator", False)
            chord_notes = midi_notes[1:] if sub_on and len(midi_notes) > 1 else midi_notes
            bass_pc = chord_notes[0] % 12 if chord_notes else -1
            update_piano_keys(_current_chord_pcs, _current_scale_pcs, bass_pc=bass_pc)
    elif not playing:
        update_piano_keys(_current_chord_pcs, _current_scale_pcs, bass_pc=-1)


# ═══════════════════════════════════════════════════════════════════════════════
# Multi-select, clipboard, drag/drop & undo/redo integration
# ═══════════════════════════════════════════════════════════════════════════════

import copy

# ── Multi-select state ─────────────────────────────────────────────────────────
_prog_selected_set: Set[int] = set()
"""Set of indices selected (in addition to the primary _prog_selected_idx)."""


def _cell_to_row_col(idx: int):
    """Convert flat cell index to (row, col)."""
    return (idx // PROG_COLS, idx % PROG_COLS)


def _range_between(idx1: int, idx2: int) -> Set[int]:
    """Return set of all cell indices in the rectangular range between two cells.
    
    The range includes all cells in the rows and columns spanned by idx1 and idx2.
    """
    r1, c1 = _cell_to_row_col(idx1)
    r2, c2 = _cell_to_row_col(idx2)
    r_min, r_max = min(r1, r2), max(r1, r2)
    c_min, c_max = min(c1, c2), max(c1, c2)
    result = set()
    for r in range(r_min, r_max + 1):
        for c in range(c_min, c_max + 1):
            idx = r * PROG_COLS + c
            if 0 <= idx < PROG_CELLS_TOTAL:
                result.add(idx)
    return result


def on_prog_cell_shift_click(sender, app_data, user_data, union=False):
    """Shift+click handler — select contiguous range from primary selection to *idx*.
    
    If union=True (Ctrl+Shift+click), adds range to existing selection instead of replacing.
    """
    idx = user_data
    if idx < 0 or idx >= len(_prog_cells):
        return
    # If there's a primary selection, select the range from it to the clicked cell
    if _prog_selected_idx is not None:
        if not union:
            _prog_selected_set.clear()
        _prog_selected_set.update(_range_between(_prog_selected_idx, idx))
    else:
        # No primary selection — just select this cell as primary
        _select_prog_cell(idx)
    _rebuild_prog_ui()


# ── Persistent paste-shape setting ──────────────────────────────────────────────

_paste_shape = "shape"
"""Default paste shape: 'linear' or 'shape'."""


def on_paste_shape_change(sender, app_data):
    """Callback when the paste-shape dropdown changes."""
    global _paste_shape
    mode_map = {
        "Linear": "linear",
        "Preserve Shape": "shape",
    }
    _paste_shape = mode_map.get(app_data, "shape")


def get_paste_shape() -> str:
    """Return the current paste shape setting."""
    return _paste_shape


def _get_selection() -> Set[int]:
    """Return the full set of selected indices (primary + multi)."""
    s = set(_prog_selected_set)
    if _prog_selected_idx is not None:
        s.add(_prog_selected_idx)
    return s


def _clear_selection():
    """Clear all multi-selection highlights."""
    _prog_selected_set.clear()


def stop_prog_sound_for_idx(idx: int):
    """Stop sound if a specific cell is currently playing."""
    global _prog_sounding_idx
    if _prog_sounding_idx == idx:
        stop_audio()
        _prog_sounding_idx = None


# ── Clipboard ──────────────────────────────────────────────────────────────────

_prog_clipboard: List[dict] = []


def on_prog_copy(sender=None, app_data=None):
    """Copy selected cell(s) or selected suggestions to clipboard."""
    global _prog_clipboard
    # If suggestions are selected, copy those with chained voice-leading
    if _sugg_selected_set and _sugg_last_suggestions:
        available_cats, cat_groups = _get_sugg_cat_groups(_sugg_last_suggestions)
        if available_cats:
            visible = cat_groups.get(available_cats[_sugg_current_cat_idx], [])
            ref = _prog_cells[_prog_selected_idx] if _prog_selected_idx is not None else None
            _prog_clipboard = []
            for i in sorted(_sugg_selected_set):
                if i < 0 or i >= len(visible):
                    continue
                s = visible[i]
                base_oct = ref.base_octave if ref and not ref.is_empty() else 3
                best_rot, best_oct = _best_voice_leading(s.root, s.quality, base_oct, ref)
                _prog_clipboard.append({
                    "root": s.root, "quality": s.quality,
                    "rotation": best_rot, "base_octave": best_oct, "voicing_idx": 0,
                })
                ref = ProgCell()
                ref.root, ref.quality = s.root, s.quality
                ref.rotation, ref.base_octave = best_rot, best_oct
            return
    sel = _get_selection()
    if not sel:
        return
    sorted_sel = sorted(sel)
    _prog_clipboard = []
    for idx in sorted_sel:
        cell = _prog_cells[idx]
        _prog_clipboard.append({
            "root": cell.root,
            "quality": cell.quality,
            "rotation": cell.rotation,
            "base_octave": cell.base_octave,
            "voicing_idx": cell.voicing_idx,
            "_idx": idx,  # store original index for shape-aware paste
        })
    # Show a brief indicator if available
    if dpg.does_item_exist("prog_detail_pos"):
        current = dpg.get_value("prog_detail_pos")
        dpg.set_value("prog_detail_pos", f"Copied {len(_prog_clipboard)} cell(s)")
        dpg.split_frame(delay=30)
        dpg.set_value("prog_detail_pos", current)


def on_prog_paste(sender=None, app_data=None):
    """Paste clipboard contents with Insert/Replace/Swap options."""
    global _prog_clipboard
    if not _prog_clipboard:
        return
    _do_paste(_prog_clipboard, get_paste_mode())


def on_prog_delete_selection(sender=None, app_data=None):
    """Delete all selected cells (with undo)."""
    from klo_chords.core.undo_manager import get_undo_manager
    um = get_undo_manager()
    sel = _get_selection()
    if not sel:
        return
    old_cells = {}
    for idx in sel:
        old_cells[idx] = copy.deepcopy(_prog_cells[idx])
        stop_prog_sound_for_idx(idx)

    def do_delete():
        for idx in sel:
            _prog_cells[idx].clear()

    def undo_delete():
        for idx, cell in old_cells.items():
            _prog_cells[idx] = cell

    um.do(do_delete, undo_delete, description="delete cells")
    _rebuild_prog_ui()


# ── Grid mutation helpers  ────────────────────────────

def _do_insert(src_idx: int, tgt_idx: int, with_undo: bool = False):
    """Insert cell at src_idx into tgt_idx.
    
    If target is empty, just fill it (no shift). Otherwise push cells down.
    """
    if src_idx == tgt_idx:
        return
    stop_prog_sound_for_idx(src_idx)
    src_data = copy.deepcopy(_prog_cells[src_idx])

    if _prog_cells[tgt_idx].is_empty():
        # Target empty — just fill it (no shift needed)
        old_tgt = copy.deepcopy(_prog_cells[tgt_idx])
        if with_undo:
            from klo_chords.core.undo_manager import get_undo_manager
            um = get_undo_manager()
            def do_fill():
                _prog_cells[tgt_idx].root = src_data.root
                _prog_cells[tgt_idx].quality = src_data.quality
                _prog_cells[tgt_idx].rotation = src_data.rotation
                _prog_cells[tgt_idx].base_octave = src_data.base_octave
                _prog_cells[tgt_idx].voicing_idx = src_data.voicing_idx
                _prog_cells[src_idx].clear()
            def undo_fill():
                _prog_cells[tgt_idx] = old_tgt
                _prog_cells[src_idx] = src_data
            um.do(do_fill, undo_fill, description="insert into empty cell")
        else:
            _prog_cells[tgt_idx].root = src_data.root
            _prog_cells[tgt_idx].quality = src_data.quality
            _prog_cells[tgt_idx].rotation = src_data.rotation
            _prog_cells[tgt_idx].base_octave = src_data.base_octave
            _prog_cells[tgt_idx].voicing_idx = src_data.voicing_idx
            _prog_cells[src_idx].clear()
        return

    # Target is non-empty — push cells down
    old_tail = [copy.deepcopy(_prog_cells[i]) for i in
                range(tgt_idx, PROG_CELLS_TOTAL)]

    if with_undo:
        from klo_chords.core.undo_manager import get_undo_manager
        um = get_undo_manager()

        def do_insert():
            for i in range(PROG_CELLS_TOTAL - 1, tgt_idx, -1):
                _prog_cells[i].root = _prog_cells[i - 1].root
                _prog_cells[i].quality = _prog_cells[i - 1].quality
                _prog_cells[i].rotation = _prog_cells[i - 1].rotation
                _prog_cells[i].base_octave = _prog_cells[i - 1].base_octave
                _prog_cells[i].voicing_idx = _prog_cells[i - 1].voicing_idx
            _prog_cells[tgt_idx].root = src_data.root
            _prog_cells[tgt_idx].quality = src_data.quality
            _prog_cells[tgt_idx].rotation = src_data.rotation
            _prog_cells[tgt_idx].base_octave = src_data.base_octave
            _prog_cells[tgt_idx].voicing_idx = src_data.voicing_idx
            _prog_cells[src_idx].clear()

        def undo_insert():
            for i, c in enumerate(old_tail):
                idx = tgt_idx + i
                if idx >= PROG_CELLS_TOTAL:
                    break
                _prog_cells[idx] = c

        um.do(do_insert, undo_insert, description="insert cell")
    else:
        for i in range(PROG_CELLS_TOTAL - 1, tgt_idx, -1):
            _prog_cells[i].root = _prog_cells[i - 1].root
            _prog_cells[i].quality = _prog_cells[i - 1].quality
            _prog_cells[i].rotation = _prog_cells[i - 1].rotation
            _prog_cells[i].base_octave = _prog_cells[i - 1].base_octave
            _prog_cells[i].voicing_idx = _prog_cells[i - 1].voicing_idx
        _prog_cells[tgt_idx].root = src_data.root
        _prog_cells[tgt_idx].quality = src_data.quality
        _prog_cells[tgt_idx].rotation = src_data.rotation
        _prog_cells[tgt_idx].base_octave = src_data.base_octave
        _prog_cells[tgt_idx].voicing_idx = src_data.voicing_idx
        _prog_cells[src_idx].clear()


def _do_replace(src_idx: int, tgt_idx: int, with_undo: bool = False):
    """Replace target cell with source cell contents."""
    if src_idx == tgt_idx:
        return
    stop_prog_sound_for_idx(src_idx)
    stop_prog_sound_for_idx(tgt_idx)
    old_src = copy.deepcopy(_prog_cells[src_idx])
    old_tgt = copy.deepcopy(_prog_cells[tgt_idx])

    if with_undo:
        from klo_chords.core.undo_manager import get_undo_manager
        um = get_undo_manager()

        def do_replace():
            _prog_cells[tgt_idx].root = old_src.root
            _prog_cells[tgt_idx].quality = old_src.quality
            _prog_cells[tgt_idx].rotation = old_src.rotation
            _prog_cells[tgt_idx].base_octave = old_src.base_octave
            _prog_cells[tgt_idx].voicing_idx = old_src.voicing_idx
            _prog_cells[src_idx].clear()

        def undo_replace():
            _prog_cells[src_idx] = old_src
            _prog_cells[tgt_idx] = old_tgt

        um.do(do_replace, undo_replace, description="replace cell")
    else:
        _prog_cells[tgt_idx].root = old_src.root
        _prog_cells[tgt_idx].quality = old_src.quality
        _prog_cells[tgt_idx].rotation = old_src.rotation
        _prog_cells[tgt_idx].base_octave = old_src.base_octave
        _prog_cells[tgt_idx].voicing_idx = old_src.voicing_idx
        _prog_cells[src_idx].clear()


def _do_swap(src_idx: int, tgt_idx: int, with_undo: bool = False):
    """Swap contents of source and target cells."""
    if src_idx == tgt_idx:
        return
    stop_prog_sound_for_idx(src_idx)
    stop_prog_sound_for_idx(tgt_idx)
    old_src = copy.deepcopy(_prog_cells[src_idx])
    old_tgt = copy.deepcopy(_prog_cells[tgt_idx])

    if with_undo:
        from klo_chords.core.undo_manager import get_undo_manager
        um = get_undo_manager()

        def do_swap():
            _prog_cells[tgt_idx].root = old_src.root
            _prog_cells[tgt_idx].quality = old_src.quality
            _prog_cells[tgt_idx].rotation = old_src.rotation
            _prog_cells[tgt_idx].base_octave = old_src.base_octave
            _prog_cells[tgt_idx].voicing_idx = old_src.voicing_idx
            _prog_cells[src_idx].root = old_tgt.root
            _prog_cells[src_idx].quality = old_tgt.quality
            _prog_cells[src_idx].rotation = old_tgt.rotation
            _prog_cells[src_idx].base_octave = old_tgt.base_octave
            _prog_cells[src_idx].voicing_idx = old_tgt.voicing_idx

        def undo_swap():
            _prog_cells[src_idx] = old_src
            _prog_cells[tgt_idx] = old_tgt

        um.do(do_swap, undo_swap, description="swap cells")
    else:
        _prog_cells[tgt_idx].root = old_src.root
        _prog_cells[tgt_idx].quality = old_src.quality
        _prog_cells[tgt_idx].rotation = old_src.rotation
        _prog_cells[tgt_idx].base_octave = old_src.base_octave
        _prog_cells[tgt_idx].voicing_idx = old_src.voicing_idx
        _prog_cells[src_idx].root = old_tgt.root
        _prog_cells[src_idx].quality = old_tgt.quality
        _prog_cells[src_idx].rotation = old_tgt.rotation
        _prog_cells[src_idx].base_octave = old_tgt.base_octave
        _prog_cells[src_idx].voicing_idx = old_tgt.voicing_idx




# ── Paste helpers ─────────────────────────────────────────────────────────────

_paste_swap_buf: list = []


def _do_paste(clipboard_data: list, mode: str):
    """Execute paste from clipboard."""
    target = _prog_selected_idx if _prog_selected_idx is not None else 0
    shape = get_paste_shape()

    from klo_chords.core.undo_manager import get_undo_manager
    um = get_undo_manager()

    if mode == "replace":
        if shape == "shape":
            _do_paste_shape_replace(clipboard_data, target, um)
        else:
            old_data = [copy.deepcopy(_prog_cells[i]) for i in
                        range(target, min(target + len(clipboard_data), PROG_CELLS_TOTAL))]
            um.do(
                do_fn=lambda: _paste_replace(clipboard_data, target),
                undo_fn=lambda: _restore_replace(old_data, target),
                description="paste (replace)"
            )
    elif mode == "insert":
        old_tail = [copy.deepcopy(_prog_cells[i]) for i in
                    range(target, PROG_CELLS_TOTAL)]
        um.do(
            do_fn=lambda: _paste_insert(clipboard_data, target),
            undo_fn=lambda: _restore_insert(old_tail, target),
            description="paste (insert)"
        )
    elif mode == "swap":
        um.do(
            do_fn=lambda: _paste_swap(clipboard_data, target),
            undo_fn=lambda: _paste_swap_backward(clipboard_data, target),
            description="paste (swap)"
        )
    _select_prog_cell(target)
    _rebuild_prog_ui()


def _compute_clipboard_shape(data: list):
    """Compute the bounding dimensions of copied cells from their stored indices."""
    indices = [d.get("_idx") for d in data if d.get("_idx") is not None]
    if not indices:
        return 1, len(data), 0, 0
    rows = [i // PROG_COLS for i in indices]
    cols = [i % PROG_COLS for i in indices]
    min_row, max_row = min(rows), max(rows)
    min_col, max_col = min(cols), max(cols)
    return (max_row - min_row + 1, max_col - min_col + 1, min_row, min_col)


def _do_paste_shape_replace(data: list, target: int, um):
    """Paste with shape preservation: maintain 2D layout of copied cells."""
    n_rows, n_cols, min_row, min_col = _compute_clipboard_shape(data)
    tr, tc = target // PROG_COLS, target % PROG_COLS

    shape_map = {}
    for d in data:
        src_idx = d.get("_idx")
        if src_idx is not None:
            sr = src_idx // PROG_COLS - min_row
            sc = src_idx % PROG_COLS - min_col
            shape_map[(sr, sc)] = d

    for d in data:
        if d.get("_idx") is None:
            for r in range(n_rows):
                for c in range(n_cols):
                    if (r, c) not in shape_map:
                        shape_map[(r, c)] = d
                        break
                if (r, c) in shape_map and shape_map[(r, c)] == d:
                    break

    old_data = {}
    for r in range(n_rows):
        for c in range(n_cols):
            idx = (tr + r) * PROG_COLS + (tc + c)
            if 0 <= idx < PROG_CELLS_TOTAL:
                old_data[(r, c)] = copy.deepcopy(_prog_cells[idx])

    def do_shape():
        for (r_offset, c_offset), cell_data in shape_map.items():
            idx = (tr + r_offset) * PROG_COLS + (tc + c_offset)
            if idx < 0 or idx >= PROG_CELLS_TOTAL:
                continue
            # Never overwrite a filled cell with an empty one from clipboard
            if cell_data.get("root") is None:
                continue
            _prog_cells[idx].root = cell_data.get("root", _prog_cells[idx].root)
            _prog_cells[idx].quality = cell_data.get("quality", _prog_cells[idx].quality)
            _prog_cells[idx].rotation = cell_data.get("rotation", 0)
            _prog_cells[idx].base_octave = cell_data.get("base_octave", 3)
            _prog_cells[idx].voicing_idx = cell_data.get("voicing_idx", 0)


    def undo_shape():
        for (r_offset, c_offset), old in old_data.items():
            idx = (tr + r_offset) * PROG_COLS + (tc + c_offset)
            if idx < 0 or idx >= PROG_CELLS_TOTAL:
                continue
            _prog_cells[idx] = old

    um.do(do_shape, undo_shape, description="paste shape (replace)")


def _paste_replace(data: list, target: int):
    for i, cell_data in enumerate(data):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        # Never overwrite a filled cell with an empty one from clipboard
        if cell_data.get("root") is None:
            continue
        _prog_cells[idx].root = cell_data["root"]
        _prog_cells[idx].quality = cell_data["quality"]
        _prog_cells[idx].rotation = cell_data.get("rotation", 0)
        _prog_cells[idx].base_octave = cell_data.get("base_octave", 3)
        _prog_cells[idx].voicing_idx = cell_data.get("voicing_idx", 0)



def _restore_replace(old_data: list, target: int):
    for i, cell in enumerate(old_data):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _prog_cells[idx] = cell
    _rebuild_prog_ui()


def _paste_insert(data: list, target: int):
    # Filter out empty clipboard entries — they should never overwrite filled cells
    filled_data = [d for d in data if d.get("root") is not None]
    n = len(filled_data)
    for i in range(PROG_CELLS_TOTAL - 1, target + n - 1, -1):
        if i >= n and i - n >= 0:
            _prog_cells[i].root = _prog_cells[i - n].root
            _prog_cells[i].quality = _prog_cells[i - n].quality
            _prog_cells[i].rotation = _prog_cells[i - n].rotation
            _prog_cells[i].base_octave = _prog_cells[i - n].base_octave
            _prog_cells[i].voicing_idx = _prog_cells[i - n].voicing_idx
    for i, cell_data in enumerate(filled_data):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _prog_cells[idx].root = cell_data["root"]
        _prog_cells[idx].quality = cell_data["quality"]
        _prog_cells[idx].rotation = cell_data.get("rotation", 0)
        _prog_cells[idx].base_octave = cell_data.get("base_octave", 3)
        _prog_cells[idx].voicing_idx = cell_data.get("voicing_idx", 0)



def _restore_insert(old_tail: list, target: int):
    for i, cell in enumerate(old_tail):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _prog_cells[idx] = cell
    _rebuild_prog_ui()


def _paste_swap(data: list, target: int):
    """Swap clipboard cells with existing cells at target position."""
    global _paste_swap_buf
    _paste_swap_buf = []
    for i, cell_data in enumerate(data):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _paste_swap_buf.append({
            "root": _prog_cells[idx].root,
            "quality": _prog_cells[idx].quality,
            "rotation": _prog_cells[idx].rotation,
            "base_octave": _prog_cells[idx].base_octave,
            "voicing_idx": _prog_cells[idx].voicing_idx,
        })
        _prog_cells[idx].root = cell_data["root"]
        _prog_cells[idx].quality = cell_data["quality"]
        _prog_cells[idx].rotation = cell_data.get("rotation", 0)
        _prog_cells[idx].base_octave = cell_data.get("base_octave", 3)
        _prog_cells[idx].voicing_idx = cell_data.get("voicing_idx", 0)


def _paste_swap_backward(data: list, target: int):
    """Undo the swap by swapping back."""
    for i, cell_data in enumerate(_paste_swap_buf):
        idx = target + i
        if idx >= PROG_CELLS_TOTAL:
            break
        _prog_cells[idx].root = cell_data["root"]
        _prog_cells[idx].quality = cell_data["quality"]
        _prog_cells[idx].rotation = cell_data["rotation"]
        _prog_cells[idx].base_octave = cell_data["base_octave"]
        _prog_cells[idx].voicing_idx = cell_data["voicing_idx"]
    _rebuild_prog_ui()

# ── Multi-cell move up/down ────────────────────────────────────────────────────

def on_prog_move_up(sender=None, app_data=None):
    """Move selection up one row."""
    from klo_chords.core.undo_manager import get_undo_manager
    um = get_undo_manager()
    sel = sorted(_get_selection())
    if not sel or sel[0] < PROG_COLS:
        return

    # Save old state
    old_states = {i: copy.deepcopy(_prog_cells[i]) for i in sel}
    target_indices = [i - PROG_COLS for i in sel]
    target_states = {i: copy.deepcopy(_prog_cells[i]) for i in target_indices}

    um.begin_batch("move up")
    for idx, tgt in zip(sel, target_indices):
        stop_prog_sound_for_idx(idx)
        swap = copy.deepcopy(_prog_cells[tgt])
        _prog_cells[tgt] = copy.deepcopy(_prog_cells[idx])
        _prog_cells[idx] = swap
    um.commit_batch()

    _rebuild_prog_ui()


def on_prog_move_down(sender=None, app_data=None):
    """Move selection down one row."""
    from klo_chords.core.undo_manager import get_undo_manager
    um = get_undo_manager()
    sel = sorted(_get_selection(), reverse=True)
    if not sel or sel[-1] >= PROG_CELLS_TOTAL - PROG_COLS:
        return

    um.begin_batch("move down")
    for idx in sel:
        tgt = idx + PROG_COLS
        if tgt < PROG_CELLS_TOTAL:
            stop_prog_sound_for_idx(idx)
            swap = copy.deepcopy(_prog_cells[tgt])
            _prog_cells[tgt] = copy.deepcopy(_prog_cells[idx])
            _prog_cells[idx] = swap
    um.commit_batch()

    _rebuild_prog_ui()


# ── Persistent paste-mode setting ───────────────────────────────────────────────

_paste_mode = "replace"
"""Default paste mode: 'insert', 'replace', or 'swap'."""


def on_paste_mode_change(sender, app_data):
    """Callback when the paste-mode dropdown changes."""
    global _paste_mode
    mode_map = {
        "Insert (push down)": "insert",
        "Replace": "replace",
        "Swap": "swap",
    }
    _paste_mode = mode_map.get(app_data, "insert")


def get_paste_mode() -> str:
    """Return the current paste mode setting."""
    return _paste_mode


# ── Undo/redo callbacks ────────────────────────────────────────────────────────

def on_undo(sender=None, app_data=None):
    """Ctrl+Z handler."""
    from klo_chords.core.undo_manager import get_undo_manager
    um = get_undo_manager()
    um.undo()
    if _prog_sounding_idx is not None and _prog_cells[_prog_sounding_idx].is_empty():
        stop_prog_sound_for_idx(_prog_sounding_idx)
        from klo_chords.audio.midi_engine import stop_midi_notes
        stop_midi_notes()
    _rebuild_prog_ui()


def on_redo(sender=None, app_data=None):
    """Ctrl+Y handler."""
    from klo_chords.core.undo_manager import get_undo_manager
    um = get_undo_manager()
    um.redo()
    _rebuild_prog_ui()


# ── Suggestion panel integration ───────────────────────────────────────────────

_SUGG_IDX_BASE           = 500   # well above the 32 grid-cell indices
_sugg_card_count         = 0
_sugg_orig_card_count    = 0     # number of pinned original cards
_sugg_current_cat_idx:   int          = 0
_sugg_last_suggestions:  list         = []
_sugg_playing_card_idx:  Optional[int] = None
_sugg_selected_set:      Set[int]     = set()   # card indices of selected suggestions
_sugg_selection_anchor:  Optional[int] = None   # anchor for Shift range-select

_SUGG_ORIG_IDX_BASE      = 900   # index space for original-card play bars (separate from category cards)
_SUGG_ORIG_CARD_IDX      = -1    # sentinel used in _sugg_playing_card_idx / _sugg_selected_set for the original card
_COLOR_ORIG_BG           = [15, 42, 22, 255]   # dark green, distinct from COLOR_CHORD_BG

_CATS_ORDERED = ["safe", "borrowed", "secondary_dominant", "chromatic_mediant", "advanced"]


def _get_sugg_cat_groups(suggestions):
    cat_groups: dict = {}
    for s in suggestions:
        cat_groups.setdefault(s.category, []).append(s)
    available = [c for c in _CATS_ORDERED if c in cat_groups]
    return available, cat_groups


_sugg_cat_text_themes: dict = {}

def _get_cat_text_theme(color):
    from klo_chords.rendering.theme import COLOR_CHORD_BG
    key = tuple(color)
    if key not in _sugg_cat_text_themes:
        with dpg.theme() as t:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,        COLOR_CHORD_BG)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, COLOR_CHORD_BG)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  COLOR_CHORD_BG)
                dpg.add_theme_color(dpg.mvThemeCol_Text,          list(color))
                dpg.add_theme_color(dpg.mvThemeCol_Border,        [65, 65, 88, 255])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding,  6, 3)
        _sugg_cat_text_themes[key] = t
    return _sugg_cat_text_themes[key]

_CAT_COLORS = {
    "safe":               [80,  200, 120, 255],
    "borrowed":           [220, 200,  60, 255],
    "secondary_dominant": [240, 160,  40, 255],
    "chromatic_mediant":  [160, 100, 220, 255],
    "advanced":           [120, 120, 120, 255],
}
_CAT_NAMES = {
    "safe":               "Safe",
    "borrowed":           "Borrowed",
    "secondary_dominant": "Secondary Dominant",
    "chromatic_mediant":  "Chromatic Mediant",
    "advanced":           "Advanced",
}


def _refresh_suggestion_panel():
    global _sugg_playing_card_idx, _sugg_selected_set, _sugg_selection_anchor
    _sugg_selected_set = set()
    _sugg_selection_anchor = None
    if _prog_selected_idx is None:
        return
    from klo_chords.core.chord_suggestions import get_suggestions, Suggestion
    suggestions = get_suggestions(
        _prog_cells, _prog_selected_idx, _prog_key, _prog_scale,
        include_sevenths=_prog_sevenths
    )
    _sugg_playing_card_idx = None

    cur = _prog_cells[_prog_selected_idx]
    has_original = not cur.is_empty()
    if has_original:
        orig = Suggestion(
            root=cur.root, quality=cur.quality,
            category="original", label="Current",
            voice_leading=0, is_original=True,
        )
        suggestions = [orig] + suggestions

    from klo_chords.rendering.chord_box import PROG_CELL_H
    panel_h = PROG_CELL_H + 44
    p = "prog_cell_detail_group"
    if not dpg.does_item_exist("suggestion_panel"):
        dpg.add_spacer(height=2, parent=p, tag="suggestion_header_spacer")
        dpg.add_text(" Suggested Chords", color=COLOR_ACCENT, parent=p,
                     tag="suggestion_header_text")
        dpg.add_separator(parent=p, tag="suggestion_separator")
        dpg.add_spacer(height=6, parent=p, tag="suggestion_spacer_btm")
        dpg.add_child_window(tag="suggestion_panel", width=-1, height=panel_h,
                              parent=p, border=False, horizontal_scrollbar=True)
        with dpg.theme() as _sugg_panel_theme:
            with dpg.theme_component(dpg.mvChildWindow):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 0, 4)
        dpg.bind_item_theme("suggestion_panel", _sugg_panel_theme)
    else:
        dpg.delete_item("suggestion_panel", children_only=True)
        dpg.configure_item("suggestion_panel", height=panel_h)

    _build_suggestion_cards(suggestions, cat_idx=0)


def _build_suggestion_cards(suggestions, cat_idx: int = 0):
    """Populate suggestion_panel with one category page of chord-cell-style cards."""
    global _sugg_card_count, _sugg_orig_card_count, _sugg_current_cat_idx, _sugg_last_suggestions
    from klo_chords.core.chords import ProgCell
    from klo_chords.rendering.chord_box import draw_prog_cell, PROG_CELL_W, PROG_CELL_H

    for i in range(_sugg_card_count):
        hreg = f"sugg_hreg_{i}"
        if dpg.does_item_exist(hreg):
            dpg.delete_item(hreg)
    for i in range(_sugg_orig_card_count):
        hreg = f"sugg_orig_hreg_{i}"
        if dpg.does_item_exist(hreg):
            dpg.delete_item(hreg)
    _sugg_card_count = 0
    _sugg_orig_card_count = 0

    _sugg_last_suggestions = suggestions
    available_cats, cat_groups = _get_sugg_cat_groups(suggestions)
    if not available_cats:
        return

    _sugg_current_cat_idx = min(cat_idx, len(available_cats) - 1)
    current_cat = available_cats[_sugg_current_cat_idx]
    visible = cat_groups[current_cat]
    color = _CAT_COLORS.get(current_cat, [200, 200, 200, 255])
    cat_label = _CAT_NAMES.get(current_cat, current_cat.replace("_", " ").title())

    card_info = []
    sg = dpg.add_group(parent="suggestion_panel", tag="suggestion_group")

    orig_suggestions = [s for s in suggestions if s.category == "original"]

    # Category navigation header — plain buttons matching detail arrow style
    hdr = dpg.add_group(parent=sg, horizontal=True)
    dpg.add_spacer(width=20, parent=hdr)
    dpg.add_button(label="<", width=25, height=22,
                   callback=lambda: _sugg_nav(-1), parent=hdr)
    dpg.add_spacer(width=6, parent=hdr)
    lbl_btn = dpg.add_button(
        label=f"{cat_label}   {_sugg_current_cat_idx + 1}/{len(available_cats)}",
        width=220, height=22, parent=hdr)
    dpg.bind_item_theme(lbl_btn, _get_cat_text_theme(color))
    dpg.add_spacer(width=6, parent=hdr)
    dpg.add_button(label=">", width=25, height=22,
                   callback=lambda: _sugg_nav(1), parent=hdr)

    dpg.add_spacer(height=4, parent=sg)

    # Card row — original card(s) first, then current category cards
    row_grp = dpg.add_group(parent=sg, horizontal=True)
    dpg.add_spacer(width=20, parent=row_grp)
    orig_info = []
    for j, s in enumerate(orig_suggestions):
        canvas_tag = f"sugg_orig_canvas_{j}"
        cell = ProgCell()
        cell.root = s.root
        cell.quality = s.quality
        cell.rotation = 0
        cell.base_octave = 3
        cell.voicing_idx = 0
        _mod = "opt" if _platform.system() == "Darwin" else "alt"
        dpg.add_drawlist(tag=canvas_tag, width=PROG_CELL_W, height=PROG_CELL_H,
                         parent=row_grp)
        draw_prog_cell(canvas_tag, cell, _SUGG_IDX_BASE + _SUGG_ORIG_IDX_BASE + j,
                       selected=False, key=_prog_key, scale=_prog_scale,
                       show_keybind=get_show_keybinds(), keybind_label=f"{_mod} + ~",
                       bg_color=_COLOR_ORIG_BG)
        dpg.add_spacer(width=6, parent=row_grp)
        orig_info.append((canvas_tag, s))
    for s in visible:
        i = len(card_info)
        canvas_tag = f"sugg_canvas_{i}"

        cell = ProgCell()
        cell.root = s.root
        cell.quality = s.quality
        cell.rotation = 0
        cell.base_octave = 3
        cell.voicing_idx = 0

        dpg.add_drawlist(tag=canvas_tag,
                         width=PROG_CELL_W, height=PROG_CELL_H,
                         parent=row_grp)
        _mod = "opt" if _platform.system() == "Darwin" else "alt"
        sugg_lbl = f"{_mod} + {i + 1}" if i < 9 else ""
        draw_prog_cell(canvas_tag, cell, _SUGG_IDX_BASE + i,
                       selected=False, key=_prog_key, scale=_prog_scale,
                       show_keybind=get_show_keybinds(), keybind_label=sugg_lbl)
        dpg.add_spacer(width=6, parent=row_grp)
        card_info.append((canvas_tag, s))

    # Register click handlers outside any group context
    for i, (canvas_tag, s) in enumerate(card_info):
        hreg_tag = f"sugg_hreg_{i}"
        with dpg.item_handler_registry(tag=hreg_tag):
            dpg.add_item_clicked_handler(callback=_make_suggestion_callback(s, i))
        dpg.bind_item_handler_registry(canvas_tag, hreg_tag)

    for j, (canvas_tag, s) in enumerate(orig_info):
        hreg_tag = f"sugg_orig_hreg_{j}"
        with dpg.item_handler_registry(tag=hreg_tag):
            dpg.add_item_clicked_handler(callback=_make_orig_suggestion_callback(s))
        dpg.bind_item_handler_registry(canvas_tag, hreg_tag)
    _sugg_orig_card_count = len(orig_info)

    _sugg_card_count = len(card_info)


def _toggle_suggestion_selection(card_idx: int):
    """Cmd/Ctrl: toggle a single card in/out of selection."""
    global _sugg_selected_set, _sugg_selection_anchor
    if card_idx in _sugg_selected_set:
        _sugg_selected_set.discard(card_idx)
    else:
        _sugg_selected_set.add(card_idx)
        _sugg_selection_anchor = card_idx
    _rebuild_sugg_selection_highlights()


def _sugg_range_select(card_idx: int):
    """Shift: select all cards between the anchor and card_idx."""
    global _sugg_selected_set, _sugg_selection_anchor
    anchor = _sugg_selection_anchor if _sugg_selection_anchor is not None else card_idx
    lo, hi = min(anchor, card_idx), max(anchor, card_idx)
    _sugg_selected_set = set(range(lo, hi + 1))
    _rebuild_sugg_selection_highlights()


def _rebuild_sugg_selection_highlights():
    from klo_chords.core.chords import ProgCell
    from klo_chords.rendering.chord_box import draw_prog_cell
    available_cats, cat_groups = _get_sugg_cat_groups(_sugg_last_suggestions)
    if not available_cats:
        return
    current_cat = available_cats[_sugg_current_cat_idx]
    for i, s in enumerate(cat_groups.get(current_cat, [])):
        canvas_tag = f"sugg_canvas_{i}"
        if not dpg.does_item_exist(canvas_tag):
            continue
        cell = ProgCell()
        cell.root, cell.quality = s.root, s.quality
        cell.rotation, cell.base_octave, cell.voicing_idx = 0, 3, 0
        _mod = "opt" if _platform.system() == "Darwin" else "alt"
        sugg_lbl = f"{_mod} + {i + 1}" if i < 9 else ""
        draw_prog_cell(canvas_tag, cell, _SUGG_IDX_BASE + i,
                       selected=(i in _sugg_selected_set),
                       key=_prog_key, scale=_prog_scale,
                       show_keybind=get_show_keybinds(), keybind_label=sugg_lbl)
        hreg_tag = f"sugg_hreg_{i}"
        if dpg.does_item_exist(hreg_tag):
            dpg.bind_item_handler_registry(canvas_tag, hreg_tag)
    orig_suggs = [s for s in _sugg_last_suggestions if s.category == "original"]
    for j, s in enumerate(orig_suggs):
        canvas_tag = f"sugg_orig_canvas_{j}"
        if not dpg.does_item_exist(canvas_tag):
            continue
        cell = ProgCell()
        cell.root, cell.quality = s.root, s.quality
        cell.rotation, cell.base_octave, cell.voicing_idx = 0, 3, 0
        _mod = "opt" if _platform.system() == "Darwin" else "alt"
        draw_prog_cell(canvas_tag, cell, _SUGG_IDX_BASE + _SUGG_ORIG_IDX_BASE + j,
                       selected=(_SUGG_ORIG_CARD_IDX in _sugg_selected_set),
                       key=_prog_key, scale=_prog_scale,
                       show_keybind=get_show_keybinds(), keybind_label=f"{_mod} + ~",
                       bg_color=_COLOR_ORIG_BG)
        hreg_tag = f"sugg_orig_hreg_{j}"
        if dpg.does_item_exist(hreg_tag):
            dpg.bind_item_handler_registry(canvas_tag, hreg_tag)


def _sugg_nav(direction: int):
    global _sugg_current_cat_idx, _sugg_playing_card_idx, _sugg_selected_set, _sugg_selection_anchor
    if not dpg.does_item_exist("suggestion_panel") or not _sugg_last_suggestions:
        return
    available_cats, _ = _get_sugg_cat_groups(_sugg_last_suggestions)
    if not available_cats:
        return
    new_idx = (_sugg_current_cat_idx + direction) % len(available_cats)
    _sugg_playing_card_idx = None
    _sugg_selected_set = set()
    _sugg_selection_anchor = None
    dpg.delete_item("suggestion_panel", children_only=True)
    _build_suggestion_cards(_sugg_last_suggestions, cat_idx=new_idx)


def _make_orig_suggestion_callback(sug):
    def callback(sender=None, app_data=None):
        global _sugg_playing_card_idx, _sugg_selected_set, _sugg_selection_anchor
        from klo_chords.widgets import dpg_keyboard
        if dpg_keyboard.shift_is_down():
            _sugg_range_select(_SUGG_ORIG_CARD_IDX)
        elif dpg_keyboard.toggle_is_down():
            _toggle_suggestion_selection(_SUGG_ORIG_CARD_IDX)
        else:
            if _sugg_playing_card_idx == _SUGG_ORIG_CARD_IDX and is_playing():
                stop_audio()
                from klo_chords.audio.midi_engine import stop_midi_notes
                stop_midi_notes()
                _sugg_playing_card_idx = None
                return
            _sugg_selected_set = {_SUGG_ORIG_CARD_IDX}
            _sugg_selection_anchor = _SUGG_ORIG_CARD_IDX
            _sugg_playing_card_idx = _SUGG_ORIG_CARD_IDX
            _apply_suggestion(sug)
            _rebuild_sugg_selection_highlights()
    return callback


def _make_suggestion_callback(sug, card_idx: int):
    def callback(sender=None, app_data=None):
        global _sugg_playing_card_idx, _sugg_selected_set, _sugg_selection_anchor
        from klo_chords.widgets import dpg_keyboard
        if dpg_keyboard.shift_is_down():
            _sugg_range_select(card_idx)
        elif dpg_keyboard.toggle_is_down():
            _toggle_suggestion_selection(card_idx)
        else:
            # Toggle off if this card is already sounding
            if card_idx == _sugg_playing_card_idx and is_playing():
                stop_audio()
                from klo_chords.audio.midi_engine import stop_midi_notes
                stop_midi_notes()
                _sugg_playing_card_idx = None
                return
            _sugg_selected_set = {card_idx}
            _sugg_selection_anchor = card_idx
            _sugg_playing_card_idx = card_idx
            _apply_suggestion(sug)
            _rebuild_sugg_selection_highlights()
    return callback


def _best_voice_leading(root: str, quality: str, base_oct: int,
                        prev_cell) -> tuple:
    """Return (rotation, octave) that minimises voice-leading distance from prev_cell."""
    from klo_chords.core.chords import QUALITY_INTERVALS
    from klo_chords.audio.sound import _stack_root_position

    if prev_cell is None or prev_cell.is_empty():
        return 0, base_oct

    prev_notes = prev_cell.get_notes()
    if not prev_notes:
        return 0, base_oct

    prev_pcs   = [note_to_pc(n) for n in prev_notes]
    prev_root  = note_to_pc(prev_cell.root)
    prev_midis = _stack_root_position(prev_pcs, prev_cell.effective_octave(), prev_root)

    intervals  = QUALITY_INTERVALS.get(quality, [0, 4, 7])
    n_rot      = len(intervals)
    root_pc    = note_to_pc(root)

    best_rot, best_oct = 0, base_oct
    best_dist = float("inf")

    for oct in range(max(0, base_oct - 1), min(9, base_oct + 2)):
        for rot in range(n_rot):
            temp = ProgCell()
            temp.root, temp.quality = root, quality
            temp.rotation, temp.base_octave, temp.voicing_idx = rot, oct, 0
            notes = temp.get_notes()
            if not notes:
                continue
            pcs   = [note_to_pc(n) for n in notes]
            midis = _stack_root_position(pcs, oct, root_pc)
            if not all(0 <= m <= 127 for m in midis):
                continue
            dist = sum(min(abs(m - p) for p in prev_midis) for m in midis)
            if dist < best_dist:
                best_dist, best_rot, best_oct = dist, rot, oct

    return best_rot, best_oct


def _apply_suggestion(sug):
    """Apply suggestion to the selected cell, play a preview, keep panel open."""
    if _prog_selected_idx is None:
        return
    from klo_chords.core.undo_manager import get_undo_manager
    um = get_undo_manager()
    old_cell = copy.deepcopy(_prog_cells[_prog_selected_idx])

    cur = _prog_cells[_prog_selected_idx]
    base_oct = cur.base_octave if not cur.is_empty() else 3

    def _non_empty(idx):
        return 0 <= idx < PROG_CELLS_TOTAL and not _prog_cells[idx].is_empty()

    left_idx = _prog_selected_idx - 1
    up_idx   = _prog_selected_idx - PROG_COLS
    if _non_empty(left_idx):
        ref = _prog_cells[left_idx]
    elif _non_empty(up_idx):
        ref = _prog_cells[up_idx]
    else:
        ref = None
        for dist in range(1, PROG_CELLS_TOTAL):
            for candidate in (_prog_selected_idx - dist, _prog_selected_idx + dist):
                if _non_empty(candidate):
                    ref = _prog_cells[candidate]
                    break
            if ref is not None:
                break

    best_rot, best_oct = _best_voice_leading(sug.root, sug.quality, base_oct, ref)

    def do_apply():
        cell = _prog_cells[_prog_selected_idx]
        cell.root       = sug.root
        cell.quality    = sug.quality
        cell.rotation   = best_rot
        cell.base_octave = best_oct
        cell.voicing_idx = 0

    def undo_apply():
        _prog_cells[_prog_selected_idx] = old_cell

    um.do(do_apply, undo_apply, description=f"apply {sug.display_name()}")
    _rebuild_prog_ui()
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx, force=True)



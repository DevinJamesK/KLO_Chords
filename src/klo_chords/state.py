"""
Application state and callback functions.

Holds the currently selected key, scale, chord list, etc.
All state mutation goes through callbacks that trigger UI refreshes.
"""

from typing import List, Optional, Set

import dearpygui.dearpygui as dpg

from klo_chords.chords import (
    ChordInfo, ProgCell, NOTE_NAMES, QUALITY_INTERVALS,
    get_diatonic_chords, get_all_voicings,
    get_scale_notes, note_to_pc, pc_to_note,
)
from klo_chords.quality import quality_spelled, quality_symbol
from klo_chords.fretboard import draw_fretboard, draw_mini_fretboard
from klo_chords.chord_box import (
    draw_chord_label, draw_prog_cell,
    PROG_QUALITY_MAP, PROG_QUALITY_REVERSE_MAP, PROG_QUALITY_NAMES,
)
from klo_chords.piano import (
    update_piano_keys, update_multi_octave_piano, clear_multi_octave_piano,
    PROG_PIANO_OCTAVES,
)
from klo_chords.sound import (
    play_chord_notes, play_progression_notes, stop_current, reset_voice_leading,
    set_base_octave, set_playback_mode, set_legato, set_volume,
    set_mode as set_sound_mode,
    is_playing, get_current_midi_notes,
    get_settings as get_sound_settings,
)
from klo_chords.theme import (
    COLOR_ACCENT, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_CHORD_BORDER,
    COLOR_ACTIVE_SPEAKER, COLOR_INACTIVE_SPEAKER,
)

# ── Constants ──────────────────────────────────────────────────────────────────
PROG_COLS = 7
PROG_ROWS = 4
PROG_CELLS_TOTAL = PROG_COLS * PROG_ROWS  # 28


def _midi_to_note_name(midi: int) -> str:
    """Convert MIDI note number to name+octave, e.g. 60 -> 'C4'."""
    pc = midi % 12
    octave = midi // 12 - 1
    name = pc_to_note(pc)
    return f"{name}{octave}"


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
_prog_sevenths  = False
_prog_cells:    List[ProgCell] = [ProgCell() for _ in range(PROG_CELLS_TOTAL)]
_prog_selected_idx: Optional[int] = None

_current_tab          = "tab_chords"
_speaker_frame_count  = 0
_prog_sounding_idx: Optional[int] = None


def state() -> dict:
    return dict(
        key=_current_key, scale=_current_scale,
        chords=_current_chords, sevenths=_include_sevenths,
        selected=_selected_chord_idx, voicing=_current_voicing_idx,
        scale_pcs=_current_scale_pcs, chord_pcs=_current_chord_pcs,
    )


# ── Play helpers ─────────────────────────────────────────────────────────────────

def _play_current_chord():
    if _selected_chord_idx is not None and _selected_chord_idx < len(_current_chords):
        play_chord_notes(_current_chords[_selected_chord_idx].notes)


def _play_prog_cell(idx: int):
    global _prog_sounding_idx
    if 0 <= idx < len(_prog_cells):
        cell = _prog_cells[idx]
        if not cell.is_empty():
            notes = cell.get_notes()
            if notes:
                play_progression_notes(notes, base_octave=cell.octave)
                _prog_sounding_idx = idx


# ── Tab switching ────────────────────────────────────────────────────────────────

def on_tab_change(sender, app_data):
    global _current_tab
    stop_current()
    _current_tab = app_data


# ── Chord tab callbacks ─────────────────────────────────────────────────────────

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


# ── Progression tab callbacks ───────────────────────────────────────────────────

def on_prog_key_change(sender, app_data):
    global _prog_key
    _prog_key = app_data


def on_prog_scale_change(sender, app_data):
    global _prog_scale
    _prog_scale = app_data


def on_prog_sevenths_toggle(sender, app_data):
    global _prog_sevenths
    _prog_sevenths = app_data


def on_prog_fill(sender=None, app_data=None):
    global _prog_cells
    chords = get_diatonic_chords(
        _prog_key, _prog_scale, include_sevenths=_prog_sevenths
    )
    for i in range(PROG_COLS):
        if i < len(chords):
            cell = _prog_cells[i]
            cell.root = chords[i].root
            cell.quality = chords[i].quality
            cell.inversion = 0
            cell.voicing_idx = 0
        else:
            _prog_cells[i].clear()
    _rebuild_progression_grid()
    # Auto-select the first cell so arrow buttons work immediately
    _select_prog_cell(0)



def on_prog_cell_click(sender, app_data, user_data):
    idx = user_data
    if 0 <= idx < len(_prog_cells):
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
        idx = NOTE_NAMES.index(cell.root) if cell.root in NOTE_NAMES else 0
        cell.root = NOTE_NAMES[(idx - 1) % 12]
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx)


def on_prog_cell_root_next(sender=None, app_data=None):
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    else:
        idx = NOTE_NAMES.index(cell.root) if cell.root in NOTE_NAMES else 0
        cell.root = NOTE_NAMES[(idx + 1) % 12]
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx)


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
    _play_prog_cell(_prog_selected_idx)


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
    _play_prog_cell(_prog_selected_idx)


def on_prog_cell_inversion_prev(sender=None, app_data=None):
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    intervals = QUALITY_INTERVALS.get(cell.quality, [0, 4, 7])
    max_inv = max(0, len(intervals) - 1)
    if max_inv > 0:
        if cell.inversion == 0:
            cell.inversion = max_inv
            cell.octave -= 1  # wrap down → go down an octave
        else:
            cell.inversion -= 1
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx)


def on_prog_cell_inversion_next(sender=None, app_data=None):
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    intervals = QUALITY_INTERVALS.get(cell.quality, [0, 4, 7])
    max_inv = max(0, len(intervals) - 1)
    if max_inv > 0:
        if cell.inversion == max_inv:
            cell.inversion = 0
            cell.octave += 1  # wrap around → go up an octave
        else:
            cell.inversion += 1
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx)


def on_prog_cell_octave_prev(sender=None, app_data=None):
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    cell.octave = max(0, cell.octave - 1)
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx)


def on_prog_cell_octave_next(sender=None, app_data=None):
    if _prog_selected_idx is None:
        return
    cell = _prog_cells[_prog_selected_idx]
    if cell.is_empty():
        cell.root = "C"
        cell.quality = "M"
    cell.octave = min(8, cell.octave + 1)
    _refresh_prog_cell(_prog_selected_idx)
    _update_prog_detail(_prog_selected_idx)
    _play_prog_cell(_prog_selected_idx)


# ── Degree helper ────────────────────────────────────────────────────────────────

def _get_degree_for_col(col: int) -> str:
    degrees = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
    return degrees[col] if 0 <= col < len(degrees) else '?'


# ── Keyboard callback ────────────────────────────────────────────────────────────

def on_key_press(sender, app_data, user_data):
    global _current_tab
    if _current_tab == "tab_chords":
        idx = user_data
        if 0 <= idx < len(_current_chords):
            global _current_voicing_idx
            _current_voicing_idx = 0
            _select_chord(idx)
            _play_current_chord()
    elif _current_tab == "tab_progression":
        idx = user_data
        if idx < PROG_COLS and idx < len(_prog_cells):
            _select_prog_cell(idx)
            _play_prog_cell(idx)


# ── Sound setting callbacks ──────────────────────────────────────────────────────

def on_sound_enable_toggle(sender, app_data):
    from klo_chords.sound import set_enabled
    set_enabled(app_data)


def on_sound_mode_change(sender, app_data):
    set_sound_mode(app_data)
    if dpg.does_item_exist("toolbar_wave_combo"):
        dpg.set_value("toolbar_wave_combo", app_data)


def on_wave_type_change(sender, app_data):
    set_sound_mode(app_data)
    if dpg.does_item_exist("sound_mode_combo"):
        dpg.set_value("sound_mode_combo", app_data)


def on_random_velocity_toggle(sender, app_data):
    from klo_chords.sound import set_random_velocity
    set_random_velocity(app_data)


def on_vel_min_change(sender, app_data):
    from klo_chords.sound import set_velocity_range
    set_velocity_range(app_data, _get_vel_max())


def on_vel_max_change(sender, app_data):
    from klo_chords.sound import set_velocity_range
    set_velocity_range(_get_vel_min(), app_data)


def on_base_octave_change(sender, app_data):
    set_base_octave(app_data)


def on_playback_mode_change(sender, app_data):
    mode_map = {"Toggle/Latch": "toggle", "One-Shot": "oneshot"}
    set_playback_mode(mode_map.get(app_data, "toggle"))
    reset_voice_leading()


def on_legato_toggle(sender, app_data):
    set_legato(app_data)
    if dpg.does_item_exist("toolbar_legato_toggle"):
        dpg.set_value("toolbar_legato_toggle", app_data)
    if dpg.does_item_exist("sound_legato_toggle"):
        dpg.set_value("sound_legato_toggle", app_data)


def on_volume_change(sender, app_data):
    set_volume(app_data)


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
        label = f"  {v_idx_display + 1}/{num_v}  "
    else:
        label = "  1/1  " if num_v == 1 else "  ---  "
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
        bass_pc = midi_notes[0] % 12
        dpg.set_value("detail_inversion", _get_inversion_name(root_pc, bass_pc))
        dpg.set_value("detail_sounding_notes", "  ".join(note_names))
    else:
        dpg.set_value("detail_inversion", "")
        dpg.set_value("detail_sounding_notes", "")


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
                                  color=COLOR_ACCENT, size=24)
                    dpg.draw_circle([30, 78], 4,
                                    fill=COLOR_INACTIVE_SPEAKER,
                                    color=COLOR_INACTIVE_SPEAKER,
                                    tag="spkr_dot_" + str(i))
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


def _refresh_prog_cell(idx: int):
    row = idx // PROG_COLS
    col = idx % PROG_COLS
    tag = f"prog_cell_{idx}"
    if dpg.does_item_exist(tag):
        cell = _prog_cells[idx] if idx < len(_prog_cells) else ProgCell()
        selected = (idx == _prog_selected_idx)
        draw_prog_cell(tag, cell, row, col, selected=selected)


def _update_prog_piano(cell: ProgCell):
    """Update the multi-octave piano with root-position voicing matching play_progression_notes."""
    notes = cell.get_notes()
    if not notes:
        clear_multi_octave_piano("prog_piano_canvas")
        if dpg.does_item_exist("prog_detail_inv_name"):
            dpg.set_value("prog_detail_inv_name", "")
        return

    base_oct = cell.octave
    centre = base_oct * 12 + 21

    pcs = [note_to_pc(n) for n in notes]

    # Root-position stacking (same as play_progression_notes)
    midi_notes = []
    for i, pc in enumerate(pcs):
        if i == 0:
            best = pc + 12
            best_dist = abs(best - centre)
            for octave in range(0, 9):
                midi = pc + 12 * octave
                dist = abs(midi - centre)
                if dist < best_dist:
                    best_dist = dist
                    best = midi
        else:
            best = midi_notes[i - 1] + 3
            best_dist = abs(best - (midi_notes[i - 1] + 5))
            for octave in range(0, 9):
                midi = pc + 12 * octave
                if midi >= midi_notes[i - 1] + 3 and midi <= midi_notes[i - 1] + 8:
                    best_dist = 0
                    best = midi
                    break
                elif midi > midi_notes[i - 1] + 3 and midi - (midi_notes[i - 1] + 5) < best_dist:
                    best_dist = abs(midi - (midi_notes[i - 1] + 5))
                    best = midi
        midi_notes.append(best)

    if midi_notes:
        avg = sum(midi_notes) // len(midi_notes)
        drift = avg - centre
        if abs(drift) > 6:
            midi_notes = [m + (-12 if drift > 6 else 12) for m in midi_notes]

    bass_midi = min(midi_notes) if midi_notes else -1

    update_multi_octave_piano("prog_piano_canvas", midi_notes, bass_midi)

    root_pc = note_to_pc(cell.root) if cell.root else -1
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
    degree = _get_degree_for_col(idx % PROG_COLS)
    dpg.set_value("prog_detail_pos", f"R{row}, C{col} ({degree})")

    if cell.is_empty():
        dpg.set_value("prog_detail_root", "C")
        dpg.set_value("prog_detail_quality", "Major")
        dpg.set_value("prog_detail_inversion", "Root")
        dpg.set_value("prog_detail_notes", "--")
        if dpg.does_item_exist("prog_detail_octave"):
            dpg.set_value("prog_detail_octave", "3")
        clear_multi_octave_piano("prog_piano_canvas")
        if dpg.does_item_exist("prog_detail_inv_name"):
            dpg.set_value("prog_detail_inv_name", "")
    else:
        dpg.set_value("prog_detail_root", cell.root)
        display_q = PROG_QUALITY_REVERSE_MAP.get(cell.quality, "Major")
        dpg.set_value("prog_detail_quality", display_q)
        inv_labels = {0: "Root", 1: "1st", 2: "2nd", 3: "3rd"}
        inv_name = inv_labels.get(cell.inversion, "Root")
        dpg.set_value("prog_detail_inversion", inv_name)
        notes_str = " ".join(cell.get_notes()) if cell.get_notes() else "--"
        dpg.set_value("prog_detail_notes", notes_str)
        if dpg.does_item_exist("prog_detail_octave"):
            dpg.set_value("prog_detail_octave", str(cell.octave))
        _update_prog_piano(cell)


def _rebuild_progression_grid():
    for idx in range(PROG_CELLS_TOTAL):
        _refresh_prog_cell(idx)
    if _prog_selected_idx is not None and _prog_selected_idx < len(_prog_cells):
        _update_prog_detail(_prog_selected_idx)


def _select_prog_cell(idx: int):
    global _prog_selected_idx
    old_idx = _prog_selected_idx
    _prog_selected_idx = idx
    if old_idx is not None and old_idx != idx:
        _refresh_prog_cell(old_idx)
    _refresh_prog_cell(idx)
    _update_prog_detail(idx)


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
    _current_chords = get_diatonic_chords(
        _current_key, _current_scale, include_sevenths=_include_sevenths
    )
    _selected_chord_idx = 0 if _current_chords else None

    if dpg.does_item_exist("scale_notes_text"):
        notes = get_scale_notes(_current_key, _current_scale)
        dpg.set_value("scale_notes_text", "  |  ".join(notes))
        _current_scale_pcs = {note_to_pc(n) for n in notes}

    reset_voice_leading()
    _rebuild_chord_list()


def _refresh_progression():
    global _prog_key, _prog_scale, _prog_cells
    if dpg.does_item_exist("prog_key_combo"):
        _prog_key = dpg.get_value("prog_key_combo")
    if dpg.does_item_exist("prog_scale_combo"):
        _prog_scale = dpg.get_value("prog_scale_combo")
    chords = get_diatonic_chords(
        _prog_key, _prog_scale, include_sevenths=_prog_sevenths
    )
    for i in range(PROG_COLS):
        if i < len(chords):
            cell = _prog_cells[i]
            cell.root = chords[i].root
            cell.quality = chords[i].quality
            cell.inversion = 0
            cell.voicing_idx = 0
        else:
            _prog_cells[i].clear()
    for i in range(PROG_COLS, PROG_CELLS_TOTAL):
        if _prog_cells[i].root is not None:
            _prog_cells[i].clear()
    _rebuild_progression_grid()
    # Auto-select the first cell so arrow buttons work immediately
    if _prog_cells and not _prog_cells[0].is_empty():
        _select_prog_cell(0)


def _refresh_speaker_indicators():
    global _speaker_frame_count, _prog_sounding_idx
    _speaker_frame_count += 1
    playing = is_playing()

    for i in range(len(_current_chords)):
        dot_tag = "spkr_dot_" + str(i)
        if not dpg.does_item_exist(dot_tag):
            continue
        is_sounding = playing and _selected_chord_idx == i
        if is_sounding:
            blink_on = (_speaker_frame_count % 6) < 4
            fill = COLOR_ACTIVE_SPEAKER if blink_on else COLOR_INACTIVE_SPEAKER
        else:
            fill = COLOR_INACTIVE_SPEAKER
        dpg.configure_item(dot_tag, fill=fill, color=fill)
        bar_tag = "chord_play_bar_" + str(i)
        if dpg.does_item_exist(bar_tag):
            try:
                dpg.configure_item(bar_tag, show=is_sounding)
            except SystemError:
                pass

    for i in range(PROG_CELLS_TOTAL):
        dot_tag = "prog_spkr_dot_" + str(i)
        if not dpg.does_item_exist(dot_tag):
            continue
        is_sounding = playing and _prog_sounding_idx == i
        if is_sounding:
            blink_on = (_speaker_frame_count % 6) < 4
            fill = COLOR_ACTIVE_SPEAKER if blink_on else COLOR_INACTIVE_SPEAKER
        else:
            fill = COLOR_INACTIVE_SPEAKER
        dpg.configure_item(dot_tag, fill=fill, color=fill)
        bar_tag = "prog_play_bar_" + str(i)
        if dpg.does_item_exist(bar_tag):
            try:
                dpg.configure_item(bar_tag, show=is_sounding)
            except SystemError:
                pass

    if not playing:
        _prog_sounding_idx = None

    _update_inversion_display()
    if playing and _selected_chord_idx is not None and _selected_chord_idx < len(_current_chords):
        midi_notes = get_current_midi_notes()
        if midi_notes:
            bass_pc = midi_notes[0] % 12
            update_piano_keys(_current_chord_pcs, _current_scale_pcs, bass_pc=bass_pc)
    elif not playing:
        update_piano_keys(_current_chord_pcs, _current_scale_pcs, bass_pc=-1)

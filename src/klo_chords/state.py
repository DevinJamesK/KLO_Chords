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
    get_scale_notes, note_to_pc, pc_to_note,
)
from klo_chords.quality import quality_spelled, quality_symbol
from klo_chords.fretboard import draw_fretboard, draw_mini_fretboard
from klo_chords.chord_box import draw_chord_label
from klo_chords.piano import update_piano_keys
from klo_chords.sound import (
    play_chord_notes, stop_current, reset_voice_leading,
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

_NOTE_NAMES_OCTAVE = {
    12: "C", 13: "C#", 14: "D", 15: "D#", 16: "E", 17: "F",
    18: "F#", 19: "G", 20: "G#", 21: "A", 22: "A#", 23: "B",
}


def _midi_to_note_name(midi: int) -> str:
    """Convert MIDI note number to name+octave, e.g. 60 → 'C4'."""
    pc = midi % 12
    octave = midi // 12 - 1
    name = pc_to_note(pc)
    return f"{name}{octave}"


# ── Global state ─────────────────────────────────────────────────────────────────
_current_key          = "C"
_current_scale        = "Major"
_current_chords:      List[ChordInfo] = []
_include_sevenths     = False
_selected_chord_idx:  Optional[int] = None
_current_voicing_idx: int = 0
_current_scale_pcs:   Set[int] = set()
_current_chord_pcs:   Set[int] = set()

# ── Progression state ────────────────────────────────────────────────────────────
_prog_key       = "C"
_prog_scale     = "Major"
_prog_sevenths  = False
_prog_chords:   List[Optional[ChordInfo]] = [None] * 8

# Speaker indicator frame counter
_speaker_frame_count = 0


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


def _play_current_chord():
    """Play the notes of the currently selected chord via sound module."""
    if _selected_chord_idx is not None and _selected_chord_idx < len(_current_chords):
        chord = _current_chords[_selected_chord_idx]
        play_chord_notes(chord.notes)


# ── Chord tab callbacks ──────────────────────────────────────────────────────────

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


# ── Progression tab callbacks ────────────────────────────────────────────────────

def on_prog_key_change(sender, app_data):
    global _prog_key
    _prog_key = app_data
    _rebuild_progression_palette()


def on_prog_scale_change(sender, app_data):
    global _prog_scale
    _prog_scale = app_data
    _rebuild_progression_palette()


def on_prog_sevenths_toggle(sender, app_data):
    global _prog_sevenths
    _prog_sevenths = app_data
    _rebuild_progression_palette()


def on_prog_fill(sender=None, app_data=None):
    """Fill the progression slots from the current diatonic scale."""
    global _prog_chords
    chords = get_diatonic_chords(
        _prog_key, _prog_scale, include_sevenths=_prog_sevenths
    )
    _prog_chords = [None] * 8
    for i, c in enumerate(chords[:8]):
        _prog_chords[i] = c
    _rebuild_progression_palette()


def on_prog_slot_click(sender, app_data, user_data):
    """Handle click on a progression chord slot."""
    idx = user_data
    if 0 <= idx < len(_prog_chords) and _prog_chords[idx] is not None:
        play_chord_notes(_prog_chords[idx].notes)


_prog_last_clicked = -1


# ── Keyboard callback (number keys 1-8) ──────────────────────────────────────────

def on_key_press(sender, app_data, user_data):
    """Handle number key presses (1-8) to select chords.

    user_data contains the chord index (0-7).
    """
    idx = user_data
    if 0 <= idx < len(_current_chords):
        global _current_voicing_idx
        _current_voicing_idx = 0
        _select_chord(idx)
        _play_current_chord()


# ── Sound setting callbacks ──────────────────────────────────────────────────────

def on_sound_enable_toggle(sender, app_data):
    from klo_chords.sound import set_enabled
    set_enabled(app_data)


def on_sound_mode_change(sender, app_data):
    set_sound_mode(app_data)
    # Keep toolbar in sync
    if dpg.does_item_exist("toolbar_wave_combo"):
        dpg.set_value("toolbar_wave_combo", app_data)


def on_wave_type_change(sender, app_data):
    """Change wave type from toolbar combo."""
    set_sound_mode(app_data)
    # Keep sound tab in sync
    if dpg.does_item_exist("sound_mode_combo"):
        dpg.set_value("sound_mode_combo", app_data)


def on_random_velocity_toggle(sender, app_data):
    from klo_chords.sound import set_random_velocity
    set_random_velocity(app_data)


def on_vel_min_change(sender, app_data):
    from klo_chords.sound import set_velocity_range
    vmax = _get_vel_max()
    set_velocity_range(app_data, vmax)


def on_vel_max_change(sender, app_data):
    from klo_chords.sound import set_velocity_range
    vmin = _get_vel_min()
    set_velocity_range(vmin, app_data)


def on_base_octave_change(sender, app_data):
    """Change the base octave for chord voicing."""
    set_base_octave(app_data)


def on_playback_mode_change(sender, app_data):
    """Change playback mode: Toggle/Latch, One-Shot.
    
    Releases all currently playing notes and resets voice leading
    so the next chord uses fresh voicing.
    """
    mode_map = {
        "Toggle/Latch": "toggle",
        "One-Shot": "oneshot",
    }
    internal = mode_map.get(app_data, "toggle")
    set_playback_mode(internal)
    reset_voice_leading()


def on_legato_toggle(sender, app_data):
    """Toggle legato mode (hold shared notes)."""
    set_legato(app_data)
    # Sync toolbar and sound tab checkboxes
    if dpg.does_item_exist("toolbar_legato_toggle"):
        dpg.set_value("toolbar_legato_toggle", app_data)
    if dpg.does_item_exist("sound_legato_toggle"):
        dpg.set_value("sound_legato_toggle", app_data)


def on_volume_change(sender, app_data):
    """Change global volume."""
    set_volume(app_data)


def _get_vel_min() -> int:
    s = get_sound_settings()
    return s["vel_min"]


def _get_vel_max() -> int:
    s = get_sound_settings()
    return s["vel_max"]


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


def _compute_midi_for_chord() -> List[int]:
    """Compute the expected MIDI note numbers for the selected chord
    using the same voice-leading logic as the sound engine,
    so the inversion display works even when sound is off."""
    from klo_chords.sound import get_settings as _gs
    if _selected_chord_idx is None or _selected_chord_idx >= len(_current_chords):
        return []
    chord = _current_chords[_selected_chord_idx]
    s = _gs()
    base_oct = s["base_octave"]
    anchor = base_oct * 12 + 21  # C in that octave
    pcs = [note_to_pc(n) for n in chord.notes]
    result = []
    for i, pc in enumerate(pcs):
        target = anchor
        if len(pcs) > 1:
            target = anchor - 12 + (i * 24 // (len(pcs) - 1))
        # Find closest MIDI to target
        candidates = [pc + 12 * o for o in range(1, 8)]
        best = min(candidates, key=lambda m: abs(m - target))
        result.append(best)
    result.sort()
    return result


def _get_inversion_name(root_pc: int, bass_pc: int) -> str:
    """Return the inversion name based on root pitch-class and bass pitch-class.
    
    Handles both triads and 7th chords:
      Root = bass is root (0)
      1st  = bass is 3rd (3 or 4 semitones from root)
      2nd  = bass is 5th (7 semitones from root)
      3rd  = bass is 7th (10 or 11 semitones from root)
    """
    for offset, name in [
        (0, "Root Position"),
        (3, "1st Inversion"),
        (4, "1st Inversion"),
        (7, "2nd Inversion"),
        (10, "3rd Inversion"),
        (11, "3rd Inversion"),
    ]:
        if bass_pc == (root_pc + offset) % 12:
            return name
    return "?"  # shouldn't happen for valid chords


def _update_inversion_display():
    """Update the inversion name and sounding notes below the keyboard.
     on shows when sound is actually playing (determined by is_playing())."""
    midi_notes = get_current_midi_notes() if is_playing() else []
    if not midi_notes or not dpg.does_item_exist("detail_inversion"):
        if dpg.does_item_exist("detail_inversion"):
            dpg.set_value("detail_inversion", "")
        if dpg.does_item_exist("detail_sounding_notes"):
            dpg.set_value("detail_sounding_notes", "")
        return

    # Get note names
    note_names = [_midi_to_note_name(m) for m in midi_notes]

    # Determine inversion from actual bass note vs chord root
    chord = _current_chords[_selected_chord_idx] if (_selected_chord_idx is not None and _selected_chord_idx < len(_current_chords)) else None
    if chord:
        root_pc = note_to_pc(chord.root)
        bass_pc = midi_notes[0] % 12
        inv_name = _get_inversion_name(root_pc, bass_pc)

        notes_str = "  ".join(note_names)
        dpg.set_value("detail_inversion", inv_name)
        dpg.set_value("detail_sounding_notes", f"({notes_str})")
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
                                  color=COLOR_ACCENT, size=20)
                    # Speaker indicator dot — visible even when inactive
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


def _rebuild_progression_palette():
    """Build/rebuild the 8 large chord slots in the Progression tab."""
    # Clear old palette items
    i = 0
    while dpg.does_item_exist("prog_slot_" + str(i)):
        dpg.delete_item("prog_slot_" + str(i))
        i += 1

    if not dpg.does_item_exist("prog_palette"):
        return

    # Build 8 slots
    for idx in range(8):
        tag = f"prog_slot_{idx}"
        chord = _prog_chords[idx] if idx < len(_prog_chords) else None

        with dpg.group(tag=tag, parent="prog_palette", horizontal=True):
            if chord is not None:
                q = quality_symbol(chord.quality).strip()
                label = f"{chord.degree} {chord.root}"
                label2 = f"{q}" if q else ""
                notes_str = "  ".join(chord.notes)
                with dpg.group():
                    dpg.add_text(label, color=COLOR_ACCENT)
                    dpg.add_text(label2, color=COLOR_TEXT)
                    dpg.add_text(notes_str, color=COLOR_TEXT_DIM)
                    dpg.add_button(label="Play", width=60, height=24,
                                   callback=on_prog_slot_click,
                                   user_data=idx)
            else:
                with dpg.group():
                    dpg.add_text("Empty", color=COLOR_TEXT_DIM)
                    dpg.add_spacer(height=4)
                    dpg.add_spacer(width=60, height=8)
            dpg.add_spacer(width=6)


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

    # Reset voice leading since the chord progression changed
    reset_voice_leading()

    _rebuild_chord_list()


def _refresh_progression():
    """Called at startup to build the progression palette."""
    global _prog_key, _prog_scale, _prog_chords
    if dpg.does_item_exist("prog_key_combo"):
        _prog_key = dpg.get_value("prog_key_combo")
    if dpg.does_item_exist("prog_scale_combo"):
        _prog_scale = dpg.get_value("prog_scale_combo")
    # Fill chords from scale first
    chords = get_diatonic_chords(
        _prog_key, _prog_scale, include_sevenths=_prog_sevenths
    )
    _prog_chords = [None] * 8
    for i, c in enumerate(chords[:8]):
        _prog_chords[i] = c
    _rebuild_progression_palette()


def _refresh_speaker_indicators():
    """Periodic callback to animate speaker indicator dots and inversion display.
    
    Updates inversion/piano bass key on EVERY frame so the green key + inversion
    info appear immediately when sound starts.
    """
    global _speaker_frame_count
    _speaker_frame_count += 1
    playing = is_playing()

    # Update speaker dots for each chord in the left panel
    for i in range(len(_current_chords)):
        dot_tag = "spkr_dot_" + str(i)
        if not dpg.does_item_exist(dot_tag):
            continue

        is_sounding = False
        if playing and _selected_chord_idx == i:
            is_sounding = True

        if is_sounding:
            blink_on = (_speaker_frame_count % 6) < 4
            fill = COLOR_ACTIVE_SPEAKER if blink_on else COLOR_INACTIVE_SPEAKER
        else:
            fill = COLOR_INACTIVE_SPEAKER

        dpg.configure_item(dot_tag, fill=fill, color=fill)

        bar_tag = "chord_play_bar_" + str(i)
        if dpg.does_item_exist(bar_tag):
            dpg.configure_item(bar_tag, show=is_sounding)

    # Update inversion display and piano bass note on EVERY frame
    _update_inversion_display()
    if playing and _selected_chord_idx is not None and _selected_chord_idx < len(_current_chords):
        midi_notes = get_current_midi_notes()
        if midi_notes:
            bass_pc = midi_notes[0] % 12
            update_piano_keys(_current_chord_pcs, _current_scale_pcs, bass_pc=bass_pc)
    elif not playing:
        update_piano_keys(_current_chord_pcs, _current_scale_pcs, bass_pc=-1)

"""
KLO Chords - Application entry point.

Builds the Dear PyGui window layout and runs the event loop.
All logic (rendering, callbacks, state) lives in sibling modules.
"""

import math
import dearpygui.dearpygui as dpg
import os

import klo_chords.prefs as prefs

from klo_chords.chords import NOTE_NAMES, SCALE_TYPES
from klo_chords.theme import (
    COLOR_ACCENT, COLOR_BG_LIGHT, COLOR_TEXT_DIM, COLOR_TEXT,
    COLOR_CHORD_BG, COLOR_CHORD_BORDER,
    font_path, font_path_fallback, icon_path,
)
from klo_chords.piano import (
    build_piano_keys, build_multi_octave_piano,
    PIANO_CANVAS_W, PIANO_CANVAS_H,
    PROG_PIANO_CANVAS_W, PROG_PIANO_CANVAS_H, PROG_PIANO_OCTAVES,
)
from klo_chords.chord_box import PROG_CELL_W, PROG_CELL_H, PROG_QUALITY_NAMES
from klo_chords.state import (
    on_key_change, on_scale_change, on_sevenths_toggle,
    on_next_voicing, on_prev_voicing, on_key_press,
    on_prog_key_change, on_prog_scale_change, on_prog_sevenths_toggle,
    on_prog_fill, on_prog_clear_all, on_prog_cell_click,
    on_prog_cell_root_prev, on_prog_cell_root_next,
    on_prog_cell_quality_prev, on_prog_cell_quality_next,
    on_prog_cell_inversion_prev, on_prog_cell_inversion_next,
    on_prog_cell_octave_prev, on_prog_cell_octave_next,
    on_prog_cell_arrow_press,
    on_sound_enable_toggle,
    on_random_velocity_toggle, on_vel_min_change, on_vel_max_change,
    on_base_octave_change, on_playback_mode_change,
    on_legato_toggle, on_volume_change,
    on_wave_type_change, on_audio_quality_change,
    on_tab_change,
    on_fretboard_mode_change, on_mute_toggle, on_stop,
    on_undo, on_redo, on_prog_copy, on_prog_paste, on_prog_delete_selection,
    on_prog_show_suggestions, on_prog_cell_shift_click,
    on_paste_mode_change, on_paste_shape_change,
    on_keybinds_toggle, get_show_keybinds,
    _refresh_chords, _refresh_progression, _refresh_speaker_indicators,
)


from klo_chords.sound import get_settings as get_sound_settings
from klo_chords.quality import quality_symbol

SCALE_NAMES = list(SCALE_TYPES.keys())

VIEWPORT_WIDTH  = 860
VIEWPORT_HEIGHT = 1000

WAVE_INTERNAL_TO_DISPLAY = {
    "triangle": "Triangle",
    "sine": "Sine",
    "sawtooth": "Sawtooth",
}
WAVE_DISPLAY_NAMES = ["Triangle", "Sine", "Sawtooth"]


def _draw_wave_preview(internal_mode: str = "triangle"):
    """Redraw the wave preview canvas showing ~2 periods centered."""
    if not dpg.does_item_exist("wave_preview"):
        return
    dpg.delete_item("wave_preview", children_only=True)

    cw, ch = 80, 28
    mid_y = ch / 2
    amp = ch / 2 - 3  # leave 3px margin top/bottom

    # Generate 2 periods of the waveform at a nice viewing frequency
    n_samples = 200
    periods = 2.0
    step = (2.0 * math.pi * periods) / n_samples

    phases = [i * step for i in range(n_samples)]

    if internal_mode == "sine":
        wave = [math.sin(p) for p in phases]
    elif internal_mode == "sawtooth":
        wave = []
        for p in phases:
            t = (p % (2.0 * math.pi)) / (2.0 * math.pi)
            wave.append(2.0 * t - 1.0)
    else:  # triangle
        wave = []
        for p in phases:
            t = (p % (2.0 * math.pi)) / (2.0 * math.pi)
            wave.append(2.0 * abs(2.0 * t - 1.0) - 1.0)

    # Normalize to canvas height with margin
    ys = [mid_y - amp * v for v in wave]
    xs = [i * cw / (n_samples - 1) for i in range(n_samples)]

    # Draw the waveform as a polyline
    points = []
    for x, y in zip(xs, ys):
        points.append(x)
        points.append(y)
    if len(points) >= 4:
        dpg.draw_polyline(points, color=COLOR_ACCENT, thickness=1.5,
                          parent="wave_preview")


def _build_toolbar():
    """Shared toolbar — called once, at the top of the window."""
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=6)
        dpg.add_text("Volume")
        snd = get_sound_settings()
        dpg.add_slider_int(tag="volume_slider",
                           default_value=int(round(snd["volume"] * 100)),
                           min_value=0, max_value=100,
                           width=120, callback=on_volume_change)
        dpg.add_spacer(width=20)
        dpg.add_text("|", color=COLOR_TEXT_DIM)
        dpg.add_spacer(width=20)
        dpg.add_text("Legato")
        snd2 = get_sound_settings()
        dpg.add_checkbox(label="", tag="toolbar_legato_toggle",
                          default_value=True,
                          callback=on_legato_toggle)
        dpg.add_spacer(width=20)
        dpg.add_text("|", color=COLOR_TEXT_DIM)
        dpg.add_spacer(width=20)
        dpg.add_text("Wave:")
        dpg.add_combo(items=WAVE_DISPLAY_NAMES,
                      default_value=WAVE_INTERNAL_TO_DISPLAY.get(snd["mode"], "Triangle"),
                      tag="toolbar_wave_combo", width=110,
                      callback=on_wave_type_change)
        dpg.add_spacer(width=6)
        with dpg.drawlist(tag="wave_preview", width=80, height=28):
            dpg.draw_rectangle([0, 0], [80, 28],
                               fill=[0, 0, 0, 0],
                               color=COLOR_TEXT_DIM)
        _draw_wave_preview(snd["mode"])
        dpg.add_spacer(width=20)
        dpg.add_text("|", color=COLOR_TEXT_DIM)
        dpg.add_spacer(width=20)
        dpg.add_checkbox(label="Show Keybinds",
                         tag="toolbar_show_keybinds",
                         default_value=False,
                         callback=on_keybinds_toggle)




def _build_chord_tab():
    """Main chord theory view."""
    # ── Key & Scale — one row across the top ────────────────────────────
    dpg.add_spacer(height=6)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=4)
        dpg.add_text("Key")
        dpg.add_spacer(width=4)
        dpg.add_combo(items=NOTE_NAMES, default_value="C",
                        tag="key_combo", width=50,
                        callback=on_key_change)
        dpg.add_spacer(width=10)
        dpg.add_text("Scale")
        dpg.add_combo(items=SCALE_NAMES, default_value="Major",
                        tag="scale_combo", width=150,
                        callback=on_scale_change)
        dpg.add_spacer(width=6)
        dpg.add_checkbox(label="Include 7th",
                            tag="sevenths_toggle", default_value=False,
                            callback=on_sevenths_toggle)
        dpg.add_spacer(width=20)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=10)
            dpg.add_text("C  |  D  |  E  |  F  |  G  |  A  |  B",
                            tag="scale_notes_text", color=COLOR_TEXT_DIM)
    dpg.add_spacer(height=6)

    with dpg.group(horizontal=True):

        # ── Left panel (just the chord list) ──────────────────────────────────
        with dpg.child_window(tag="left_panel", width=380,
                              height=-1, border=True):
            dpg.add_text("Diatonic Chords", color=COLOR_ACCENT)

            with dpg.group(tag="chord_list_scroll"):
                dpg.add_spacer(height=6)

            # Hint about number keys — centered in left panel
            dpg.add_spacer(height=20)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=60)
                with dpg.group():
                    dpg.add_text("Press 1-7 to play chords.", color=COLOR_TEXT_DIM)
                    dpg.add_text("Press same chord again to stop sound.", color=COLOR_TEXT_DIM)
                    dpg.add_text("Spacebar will stop the current sound.", color=COLOR_TEXT_DIM)
                    dpg.add_text("ESC will toggle mute.", color=COLOR_TEXT_DIM)

        # ── Right panel ──────────────────────────────────────────────────────
        with dpg.child_window(tag="right_panel", width=-1,
                              height=-1, border=True):
            dpg.add_text("Chord Detail", color=COLOR_ACCENT)
            dpg.add_spacer(height=2)

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=20)
                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_text("Degree / Root:", color=COLOR_TEXT_DIM)
                        dpg.add_text("--", tag="detail_root", color=COLOR_ACCENT)
                    dpg.add_spacer(height=2)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Quality:", color=COLOR_TEXT_DIM)
                        dpg.add_text("--", tag="detail_quality",
                                     color=COLOR_ACCENT)
                    dpg.add_spacer(height=2)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Notes:", color=COLOR_TEXT_DIM)
                        dpg.add_text("--", tag="detail_notes", color=COLOR_ACCENT)
                    dpg.add_spacer(height=2)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Intervals:", color=COLOR_TEXT_DIM)
                        dpg.add_text("--", tag="detail_intervals",
                                     color=COLOR_TEXT_DIM)
                    dpg.add_spacer(height=6)
            
            dpg.add_text("Keyboard", color=COLOR_ACCENT)
            dpg.add_spacer(height=6)

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=20)
                with dpg.drawlist(tag="piano_canvas",
                                  width=PIANO_CANVAS_W,
                                  height=PIANO_CANVAS_H):
                    pass

            # Inversion display — shows which notes are sounding
            dpg.add_spacer(height=6)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=20)
                dpg.add_text("", tag="detail_inversion",
                             color=COLOR_TEXT)
                dpg.add_spacer(width=6)
                dpg.add_text("", tag="detail_sounding_notes",
                             color=COLOR_TEXT_DIM)
            dpg.add_spacer(height=6)
            dpg.add_text("Fretboard", color=COLOR_ACCENT)
            dpg.add_spacer(height=6)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=20)
                with dpg.drawlist(width=360, height=220,
                                  tag="fretboard_canvas"):
                    dpg.draw_rectangle([0, 0], [360, 220],
                                       fill=COLOR_BG_LIGHT,
                                       color=COLOR_BG_LIGHT,
                                       tag="fretboard_bg")


            dpg.add_spacer(height=4)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=20)
                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="<  Prev", width=80,
                                       callback=on_prev_voicing)
                        dpg.add_text("", tag="voicing_label",
                                     color=COLOR_ACCENT)
                        dpg.add_button(label="Next  >", width=80,
                                       callback=on_next_voicing)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=20)
                dpg.add_checkbox(label="Show Note Names",
                                tag="fretboard_mode_toggle",
                                default_value=False,
                                callback=on_fretboard_mode_change)



def _build_progression_tab():
    """Chord progression tab with 7x4 grid of clickable cells."""
    PROG_COLS = 7
    PROG_ROWS = 4

    # ── Scale chooser — centered row ───────────────────────────────────────
    dpg.add_spacer(height=6)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=4)
        dpg.add_text("Key")
        dpg.add_spacer(width=4)
        dpg.add_combo(items=NOTE_NAMES, default_value="C",
                      tag="prog_key_combo", width=50,
                      callback=on_prog_key_change)
        dpg.add_spacer(width=10)
        dpg.add_text("Scale")
        dpg.add_combo(items=SCALE_NAMES, default_value="Major",
                      tag="prog_scale_combo", width=150,
                      callback=on_prog_scale_change)
        dpg.add_spacer(width=6)
        dpg.add_checkbox(label="Include 7th",
                         tag="prog_sevenths_toggle",
                         default_value=False,
                         callback=on_prog_sevenths_toggle)
        dpg.add_spacer(width=20)
        dpg.add_button(label="Fill Chords", width=100,
                       tag="prog_fill_btn", callback=on_prog_fill)
        dpg.add_spacer(width=10)
        dpg.add_button(label="Clear All", width=100,
                       tag="prog_clear_btn", callback=on_prog_clear_all)

    dpg.add_spacer(height=4)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=4)
        dpg.add_text("Paste Mode", color=COLOR_TEXT_DIM)
        dpg.add_combo(items=["Insert", "Replace", "Swap"],
                      default_value="Replace",
                      tag="paste_mode_combo", width=100,
                      callback=on_paste_mode_change)
        dpg.add_spacer(width=20)
        dpg.add_text("Paste Shape:", color=COLOR_TEXT_DIM)
        dpg.add_combo(items=["Linear", "Preserve Shape"],
                      default_value="Preserve Shape",
                      tag="paste_shape_combo", width=150,
                      callback=on_paste_shape_change)

    dpg.add_spacer(height=2)
    dpg.add_text(" Chord Grid (click to edit/play)", color=COLOR_ACCENT)
    dpg.add_separator()
    dpg.add_spacer(height=8)

    # ── 7x4 grid — centered ────────────────────────────────────────────────
    # Grid: 7 cells × 88px + 6 gaps × 6px = 652px
    GRID_TOTAL_W = PROG_COLS * PROG_CELL_W + (PROG_COLS - 1) * 6
    GRID_PAD = 20
    for row in range(PROG_ROWS):
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=GRID_PAD)
            with dpg.group(tag=f"prog_grid_row_{row}", horizontal=True):
                for col in range(PROG_COLS):
                    idx = row * PROG_COLS + col
                    tag_canvas = f"prog_cell_{idx}"
                    with dpg.drawlist(tag=tag_canvas,
                                      width=PROG_CELL_W,
                                      height=PROG_CELL_H):
                        pass
                    with dpg.item_handler_registry(tag=f"prog_click_hreg_{idx}"):
                        dpg.add_item_clicked_handler(
                            callback=on_prog_cell_click, user_data=idx
                        )
                    dpg.bind_item_handler_registry(tag_canvas,
                                                   f"prog_click_hreg_{idx}")
                    if col < PROG_COLS - 1:
                        dpg.add_spacer(width=6)
        dpg.add_spacer(height=6)

    # ── Cell detail panel (below the grid) ──────────────────────────────────
    dpg.add_spacer(height=2)
    dpg.add_text(" Cell Detail", color=COLOR_ACCENT)
    dpg.add_separator()
    dpg.add_spacer(height=4)

    with dpg.group(tag="prog_cell_detail_group", show=True):
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=24)
            dpg.add_text("Selected: ", color=COLOR_TEXT_DIM)
            dpg.add_text("None", tag="prog_detail_pos", color=COLOR_ACCENT)

        dpg.add_spacer(height=4)

        # Root: < btn + text + > btn
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=24)
            dpg.add_text("Root:", color=COLOR_TEXT_DIM)
            dpg.add_spacer(width=4)
            dpg.add_button(label="<", width=26, height=22,
                           tag="prog_root_prev_btn",
                           callback=on_prog_cell_root_prev)
            dpg.add_text("C", tag="prog_detail_root", color=COLOR_ACCENT)
            dpg.add_button(label=">", width=26, height=22,
                           tag="prog_root_next_btn",
                           callback=on_prog_cell_root_next)
            dpg.add_spacer(width=16)

            dpg.add_text("Quality:", color=COLOR_TEXT_DIM)
            dpg.add_spacer(width=4)
            dpg.add_button(label="<", width=26, height=22,
                           tag="prog_quality_prev_btn",
                           callback=on_prog_cell_quality_prev)
            dpg.add_text("Major", tag="prog_detail_quality", color=COLOR_ACCENT)
            dpg.add_button(label=">", width=26, height=22,
                           tag="prog_quality_next_btn",
                           callback=on_prog_cell_quality_next)
            dpg.add_spacer(width=16)

            dpg.add_text("Inversion:", color=COLOR_TEXT_DIM)
            dpg.add_spacer(width=4)
            dpg.add_button(label="<", width=26, height=22,
                           tag="prog_inv_prev_btn",
                           callback=on_prog_cell_inversion_prev)
            dpg.add_text("Root", tag="prog_detail_inversion", color=COLOR_ACCENT)
            dpg.add_button(label=">", width=26, height=22,
                           tag="prog_inv_next_btn",
                           callback=on_prog_cell_inversion_next)
            dpg.add_spacer(width=16)

            dpg.add_text("Octave:", color=COLOR_TEXT_DIM)
            dpg.add_spacer(width=4)
            dpg.add_button(label="<", width=26, height=22,
                           tag="prog_octave_prev_btn",
                           callback=on_prog_cell_octave_prev)
            dpg.add_text("3", tag="prog_detail_octave", color=COLOR_ACCENT)
            dpg.add_button(label=">", width=26, height=22,
                           tag="prog_octave_next_btn",
                           callback=on_prog_cell_octave_next)

        dpg.add_spacer(height=4)
        dpg.add_button(label="Show Suggestions", tag="prog_suggest_btn",
                        width=180, height=24, callback=on_prog_show_suggestions)
        dpg.add_spacer(height=4)

        _piano_pad = 20
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=24)
            dpg.add_text("Notes:", color=COLOR_TEXT_DIM)
            dpg.add_text("--", tag="prog_detail_notes", color=COLOR_ACCENT)
            #dpg.add_spacer(width=16)
            dpg.add_spacer(width=_piano_pad)
            dpg.add_text("", tag="prog_detail_inv_name", color=COLOR_TEXT)

        # ── Multi-octave piano for cell detail (centered) ─────────────────
        dpg.add_spacer(height=8)

       
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=_piano_pad)
            with dpg.drawlist(tag="prog_piano_canvas",
                              width=PROG_PIANO_CANVAS_W,
                              height=PROG_PIANO_CANVAS_H):
                pass


def _build_sound_tab():
    """Sound settings."""
    with dpg.child_window(tag="sound_panel", width=-1,
                          height=-1, border=True):
        dpg.add_text("Sound Settings", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=6)

        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_checkbox(label="Enable sound",
                             tag="sound_enable", default_value=True,
                             callback=on_sound_enable_toggle)
            dpg.add_spacer(width=20)
            dpg.add_text("|", color=COLOR_TEXT_DIM)
            dpg.add_spacer(width=20)
            dpg.add_text("Wave type:")
            snd = get_sound_settings()
            dpg.add_combo(items=WAVE_DISPLAY_NAMES,
                          default_value=WAVE_INTERNAL_TO_DISPLAY.get(snd["mode"], "Triangle"),
                          tag="sound_mode_combo", width=120,
                          callback=on_wave_type_change)

        dpg.add_spacer(height=10)

        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_text("Audio Quality:")
            dpg.add_spacer(width=6)
            quality_display = {"smooth": "Smooth", "responsive": "Responsive", "legacy": "Legacy"}
            snd2 = get_sound_settings()
            dpg.add_combo(items=["Smooth", "Responsive", "Legacy"],
                          default_value=quality_display.get(snd2.get("audio_quality", "smooth"), "Smooth"),
                          tag="sound_quality_combo", width=120,
                          callback=on_audio_quality_change)

        dpg.add_spacer(height=12)
        dpg.add_text("Velocity", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_checkbox(label="Random velocity per note",
                             tag="random_vel", default_value=True,
                             callback=on_random_velocity_toggle)
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_text("Min:", color=COLOR_TEXT_DIM)
            dpg.add_slider_int(tag="vel_min_slider",
                               default_value=60,
                               min_value=1, max_value=127,
                               width=200, callback=on_vel_min_change)
            dpg.add_spacer(width=24)
            dpg.add_text("Max:", color=COLOR_TEXT_DIM)
            dpg.add_slider_int(tag="vel_max_slider",
                               default_value=100,
                               min_value=1, max_value=127,
                               width=200, callback=on_vel_max_change)

        dpg.add_spacer(height=12)
        dpg.add_text("Playback Mode", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=16)
            dpg.add_combo(items=["Toggle/Latch", "One-Shot"],
                          default_value="Toggle/Latch",
                          tag="playback_mode_combo", width=140,
                          callback=on_playback_mode_change)
            dpg.add_spacer(width=10)
            dpg.add_text("Toggle=on/off per chord, One-Shot=~1s",
                         color=COLOR_TEXT_DIM)

        dpg.add_spacer(height=12)
        dpg.add_text("Base Octave", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=16)
            dpg.add_text("Lower", color=COLOR_TEXT_DIM)
            dpg.add_slider_int(tag="base_octave_slider",
                               default_value=3,
                               min_value=2, max_value=6,
                               width=300,
                               callback=on_base_octave_change)
            dpg.add_text("Higher", color=COLOR_TEXT_DIM)

        dpg.add_spacer(height=12)
        dpg.add_text("Legato Mode", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=16)
            dpg.add_checkbox(label="Hold shared notes when switching chords",
                              tag="sound_legato_toggle", default_value=True,
                              callback=on_legato_toggle)
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_text("When enabled, notes common to both chords stay held,"
                         " only the differing notes change. Smoother transitions.",
                          color=COLOR_TEXT_DIM, wrap=480)


def build_ui():
    dpg.create_context()
    dpg.configure_app()

    with dpg.font_registry():
        path = font_path()
        if os.path.exists(path):
            dpg.add_font(path, 20)
        fallback = font_path_fallback()
        if os.path.exists(fallback):
            dpg.add_font(fallback, 20)

    with dpg.window(tag="main_win", no_close=True, no_collapse=True,
                    no_scrollbar=True, width=-1, height=-1):

        # ── Shared toolbar (visible on every page) ──────────────────────────
        dpg.add_spacer(height=4)
        _build_toolbar()
        dpg.add_separator()
        dpg.add_spacer(height=6)

        with dpg.tab_bar(tag="main_tab_bar",
                         callback=on_tab_change):
            with dpg.tab(label="Chords", tag="tab_chords"):
                _build_chord_tab()

            with dpg.tab(label="Progression", tag="tab_progression"):
                _build_progression_tab()

            with dpg.tab(label="Sound", tag="tab_sound"):
                _build_sound_tab()

    # ── Theme ──────────────────────────────────────────────────────────────────
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 6, 6)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 4, 4)

    dpg.bind_theme(global_theme)

    # ── Viewport ────────────────────────────────────────────────────────────────
    dpg.create_viewport(title="KLO Chords", width=VIEWPORT_WIDTH,
                        height=VIEWPORT_HEIGHT, resizable=False,
                        decorated=True)
    ico = icon_path()
    if os.path.exists(ico):
        dpg.set_viewport_large_icon(ico)
        dpg.set_viewport_small_icon(ico)
    dpg.setup_dearpygui()
    dpg.set_primary_window("main_win", True)
    dpg.show_viewport()

    # Sexy "Fill" button styling
    if dpg.does_item_exist("prog_fill_btn"):
        with dpg.theme() as fill_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,
                                    [50, 120, 200, 255])   # blue bg
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,
                                    [60, 150, 240, 255])   # lighter on hover
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,
                                    [30, 90, 170, 255])    # darker when pressed
                dpg.add_theme_color(dpg.mvThemeCol_Text,
                                    [255, 255, 255, 255])   # white text
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
        dpg.bind_item_theme("prog_fill_btn", fill_theme)

    # "Clear All" button styling (slightly different shade)
    if dpg.does_item_exist("prog_clear_btn"):
        with dpg.theme() as clear_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,
                                    [180, 50, 50, 255])    # red bg
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,
                                    [220, 60, 60, 255])    # lighter on hover
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,
                                    [140, 30, 30, 255])    # darker when pressed
                dpg.add_theme_color(dpg.mvThemeCol_Text,
                                    [255, 255, 255, 255])   # white text
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
        dpg.bind_item_theme("prog_clear_btn", clear_theme)

    # ── Initialize ──────────────────────────────────────────────────────────────
    build_piano_keys("piano_canvas")
    build_multi_octave_piano("prog_piano_canvas")
    _refresh_chords()
    _refresh_progression()

    # ── Keyboard handlers ──────────────────────────────────────────────────────
    with dpg.handler_registry(tag="main_handler_registry"):
        # Row 0 (cells 0-6): keys 1-7, then QWERTY rows for cells 7-27
        PROG_KEY_CELL_MAP = [
            # Row 0: 1-7
            (dpg.mvKey_1, 0), (dpg.mvKey_2, 1), (dpg.mvKey_3, 2),
            (dpg.mvKey_4, 3), (dpg.mvKey_5, 4), (dpg.mvKey_6, 5),
            (dpg.mvKey_7, 6),
            # Row 1: Q W E R T Y U
            (dpg.mvKey_Q, 7), (dpg.mvKey_W, 8), (dpg.mvKey_E, 9),
            (dpg.mvKey_R, 10), (dpg.mvKey_T, 11), (dpg.mvKey_Y, 12),
            (dpg.mvKey_U, 13),
            # Row 2: A S D F G H J
            (dpg.mvKey_A, 14), (dpg.mvKey_S, 15), (dpg.mvKey_D, 16),
            (dpg.mvKey_F, 17), (dpg.mvKey_G, 18), (dpg.mvKey_H, 19),
            (dpg.mvKey_J, 20),
            # Row 3: Z X C V B N M
            (dpg.mvKey_Z, 21), (dpg.mvKey_X, 22), (dpg.mvKey_C, 23),
            (dpg.mvKey_V, 24), (dpg.mvKey_B, 25), (dpg.mvKey_N, 26),
            (dpg.mvKey_M, 27),
        ]
        for key, cell_idx in PROG_KEY_CELL_MAP:
            dpg.add_key_press_handler(key=key, callback=on_key_press, user_data=cell_idx)
        # Escape / Spacebar
        dpg.add_key_press_handler(key=dpg.mvKey_Escape, callback=on_mute_toggle)
        dpg.add_key_press_handler(key=dpg.mvKey_Spacebar, callback=on_stop)
        # Arrow keys: Left/Right = inversion, Up/Down = quality (progression tab)
        dpg.add_key_press_handler(key=dpg.mvKey_Left,  callback=on_prog_cell_arrow_press, user_data="inv_prev")
        dpg.add_key_press_handler(key=dpg.mvKey_Right, callback=on_prog_cell_arrow_press, user_data="inv_next")
        dpg.add_key_press_handler(key=dpg.mvKey_Up,    callback=on_prog_cell_arrow_press, user_data="quality_prev")
        dpg.add_key_press_handler(key=dpg.mvKey_Down,  callback=on_prog_cell_arrow_press, user_data="quality_next")
        # Ctrl+Z/Y = Undo/Redo; Ctrl+C/V = Copy/Paste; Ctrl+K = Show Keybinds
        dpg.add_key_press_handler(key=dpg.mvKey_Z, callback=_on_key_with_ctrl, user_data="undo")
        dpg.add_key_press_handler(key=dpg.mvKey_Y, callback=_on_key_with_ctrl, user_data="redo")
        dpg.add_key_press_handler(key=dpg.mvKey_C, callback=_on_key_with_ctrl, user_data="copy")
        dpg.add_key_press_handler(key=dpg.mvKey_V, callback=_on_key_with_ctrl, user_data="paste")
        dpg.add_key_press_handler(key=dpg.mvKey_K, callback=_on_key_with_ctrl, user_data="keybinds")
        # Delete key
        dpg.add_key_press_handler(key=dpg.mvKey_Delete, callback=on_prog_delete_selection)


    from klo_chords import dpg_keyboard
    dpg_keyboard.setup()

    # ── Main loop ──────────────────────────────────────────────────────────────
    while dpg.is_dearpygui_running():
        dpg_keyboard.poll()
        _refresh_speaker_indicators()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


# ── Keyboard shortcut helpers ────────────────────────────────────────────────────


def _on_key_with_ctrl(sender, app_data, user_data):
    """Handle key presses that require platform-native modifier (Ctrl on Win, Cmd on Mac)."""
    from klo_chords import dpg_keyboard
    if not dpg_keyboard.toggle_is_down():
        return
    action = user_data
    if action == "undo":
        on_undo()
    elif action == "redo":
        on_redo()
    elif action == "copy":
        on_prog_copy()
    elif action == "paste":
        on_prog_paste()
    elif action == "keybinds":
        on_keybinds_toggle()



def main():
    try:
        # Load persisted preferences and apply to sound engine before UI builds
        _apply_preferences()
        build_ui()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


def _apply_preferences():
    """Read preferences.json and push values into the sound engine."""
    prefs_data = prefs.load()
    from klo_chords.sound import (
        set_volume, set_enabled, set_mode,
        set_audio_quality, set_legato, set_playback_mode,
        set_random_velocity, set_velocity_range, set_base_octave,
    )
    set_volume(prefs_data.get("volume", 75) / 100.0)
    set_enabled(prefs_data.get("sound_enabled", True))
    set_mode(prefs_data.get("wave", "triangle"))
    set_audio_quality(prefs_data.get("audio_quality", "smooth"))
    set_legato(prefs_data.get("legato", True))
    set_playback_mode(prefs_data.get("playback_mode", "toggle"))
    set_random_velocity(prefs_data.get("random_velocity", True))
    set_velocity_range(prefs_data.get("vel_min", 60),
                       prefs_data.get("vel_max", 100))
    set_base_octave(prefs_data.get("base_octave", 3))


if __name__ == "__main__":
    main()

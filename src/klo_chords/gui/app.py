"""
KLO Chords - Application entry point.

Builds the Dear PyGui window layout and runs the event loop.
All logic (rendering, callbacks, state) lives in sibling modules.
"""

from __future__ import annotations

import math
import platform
import dearpygui.dearpygui as dpg
import os

# On macOS Retina displays the physical pixel density is 2× the logical size.
# Baking the font atlas at 2× then halving the global scale gives crisp text.
# draw_text() uses explicit pixel sizes and is unaffected by global font scale.
_DISPLAY_SCALE = 2.0 if platform.system() == "Darwin" else 1.0

import klo_chords.core.prefs as prefs

from klo_chords.core.chords import KEY_NAMES, SCALE_TYPES
from klo_chords.rendering.theme import (
    COLOR_ACCENT, COLOR_BG_LIGHT, COLOR_TEXT_DIM, COLOR_TEXT,
    WAVE_INTERNAL_TO_DISPLAY, WAVE_DISPLAY_NAMES,
    COLOR_CHORD_BG, COLOR_CHORD_BORDER,
    font_path, font_path_fallback, icon_path,
    set_draw_font,
)
from klo_chords.rendering.piano import (
    build_piano_keys, build_multi_octave_piano,
    PIANO_CANVAS_W, PIANO_CANVAS_H,
    PROG_PIANO_CANVAS_W, PROG_PIANO_CANVAS_H, PROG_PIANO_OCTAVES,
)
from klo_chords.rendering.chord_box import PROG_CELL_W, PROG_CELL_H, PROG_QUALITY_NAMES
from klo_chords.state import (
    on_key_change, on_scale_change, on_sevenths_toggle,
    on_next_voicing, on_prev_voicing, on_key_press,
    on_prog_key_change, on_prog_scale_change, on_prog_sevenths_toggle,
    on_prog_fill, on_prog_clear_all, on_prog_export, on_prog_import, on_prog_cell_click,
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
    on_audio_device_change,
    on_tab_change,
    on_fretboard_mode_change, on_mute_toggle, on_stop,
    on_undo, on_redo, on_prog_copy, on_prog_paste, on_prog_delete_selection,
    on_paste_mode_change, on_paste_shape_change,
    on_keybinds_toggle, get_show_keybinds, init_show_keybinds,
    on_jazz_symbols_toggle, get_use_jazz_symbols, init_use_jazz_symbols,
    on_sub_oscillator_toggle, on_reset_prefs,
    _refresh_chords, _refresh_progression, _refresh_speaker_indicators,
)


from klo_chords.audio.sound import get_settings as get_sound_settings
import klo_chords.audio.midi_engine as midi_tab
from klo_chords.core.quality import quality_symbol

SCALE_NAMES = list(SCALE_TYPES.keys())

_IS_WINDOWS = platform.system() == "Windows"
VIEWPORT_WIDTH  = 880 if _IS_WINDOWS else 860
VIEWPORT_HEIGHT = 1030 if _IS_WINDOWS else 1000


def _draw_wave_preview(internal_mode: str = "triangle"):
    """Redraw the wave preview canvas showing ~2 periods centered."""
    if not dpg.does_item_exist("wave_preview"):
        return
    dpg.delete_item("wave_preview", children_only=True)

    cw, ch = 36, 28
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
        sound_cfg = get_sound_settings()
        dpg.add_slider_int(tag="volume_slider",
                           default_value=int(round(sound_cfg["volume"] * 100)),
                           min_value=0, max_value=100,
                           width=100, callback=on_volume_change)
        dpg.add_spacer(width=8)
        dpg.add_text("|", color=COLOR_TEXT_DIM)
        dpg.add_spacer(width=8)
        dpg.add_text("Legato")
        sound_cfg2 = get_sound_settings()
        dpg.add_checkbox(label="", tag="toolbar_legato_toggle",
                          default_value=True,
                          callback=on_legato_toggle)
        dpg.add_spacer(width=8)
        dpg.add_text("|", color=COLOR_TEXT_DIM)
        dpg.add_spacer(width=8)
        dpg.add_text("Wave:")
        dpg.add_combo(items=WAVE_DISPLAY_NAMES,
                      default_value=WAVE_INTERNAL_TO_DISPLAY.get(sound_cfg["mode"], "Triangle"),
                      tag="toolbar_wave_combo", width=110,
                      callback=on_wave_type_change)
        dpg.add_spacer(width=16)
        dpg.add_checkbox(label="Add Bass Root Note",
                         tag="toolbar_sub_osc_toggle",
                         default_value=get_sound_settings().get("sub_oscillator", True),
                         callback=on_sub_oscillator_toggle)
        dpg.add_spacer(width=8)
        dpg.add_text("|", color=COLOR_TEXT_DIM)
        dpg.add_spacer(width=8)
        dpg.add_checkbox(label="Show Keybinds",
                         tag="toolbar_show_keybinds",
                         default_value=get_show_keybinds(),
                         callback=on_keybinds_toggle)
    dpg.add_spacer(height=8)




def _build_chord_tab():
    """Main chord theory view."""
    # ── Key & Scale — one row across the top ────────────────────────────
    dpg.add_spacer(height=6)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        dpg.add_text("Key")
        dpg.add_combo(items=KEY_NAMES, default_value="C",
                        tag="key_combo", width=50,
                        callback=on_key_change)
        dpg.add_spacer(width=10)
        dpg.add_text("Scale")
        dpg.add_combo(items=SCALE_NAMES, default_value="Major",
                        tag="scale_combo", width=150,
                        callback=on_scale_change)
        dpg.add_spacer(width=10)
        dpg.add_checkbox(label="Include 7th",
                            tag="sevenths_toggle", default_value=False,
                            callback=on_sevenths_toggle)
        dpg.add_spacer(width=75)
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
                        dpg.add_button(label="\u25c0  Prev", width=80,
                                       callback=on_prev_voicing)
                        dpg.add_text("", tag="voicing_label",
                                     color=COLOR_ACCENT)
                        dpg.add_button(label="Next  \u25b6", width=80,
                                       callback=on_next_voicing)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=20)
                dpg.add_checkbox(label="Show Note Names",
                                tag="fretboard_mode_toggle",
                                default_value=False,
                                callback=on_fretboard_mode_change)



def _build_progression_tab():
    """Chord progression tab with 8x4 grid of clickable cells."""
    PROG_COLS = 8
    PROG_ROWS = 4

    # ── Scale chooser — centered row ───────────────────────────────────────
    dpg.add_spacer(height=6)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        dpg.add_text("Key")
        dpg.add_combo(items=KEY_NAMES, default_value="C",
                      tag="prog_key_combo", width=50,
                      callback=on_prog_key_change)
        dpg.add_spacer(width=10)
        dpg.add_text("Scale")
        dpg.add_combo(items=SCALE_NAMES, default_value="Major",
                      tag="prog_scale_combo", width=150,
                      callback=on_prog_scale_change)
        dpg.add_spacer(width=10)
        dpg.add_checkbox(label="Include 7th",
                         tag="prog_sevenths_toggle",
                         default_value=True,
                         callback=on_prog_sevenths_toggle)
        dpg.add_spacer(width=18)
        dpg.add_button(label="Fill Chords", width=86,
                       tag="prog_fill_btn", callback=on_prog_fill)
        dpg.add_spacer(width=6)
        dpg.add_button(label="Clear All", width=86,
                       tag="prog_clear_btn", callback=on_prog_clear_all)
        dpg.add_spacer(width=6)
        dpg.add_button(label="Import", width=72,
                       tag="prog_import_btn", callback=on_prog_import)
        dpg.add_spacer(width=6)
        dpg.add_button(label="Export", width=72,
                       tag="prog_export_btn", callback=on_prog_export)


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
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        dpg.add_text("Paste Mode", color=COLOR_TEXT_DIM)
        dpg.add_spacer(width=6)
        dpg.add_combo(items=["Insert", "Replace", "Swap"],
                      default_value="Replace",
                      tag="paste_mode_combo", width=108,
                      callback=on_paste_mode_change)
        dpg.add_spacer(width=8)
        dpg.add_text("Paste Shape", color=COLOR_TEXT_DIM)
        dpg.add_combo(items=["Linear", "Preserve Shape"],
                      default_value="Preserve Shape",
                      tag="paste_shape_combo", width=120,
                      callback=on_paste_shape_change)
    dpg.add_spacer(height=2)
    dpg.add_text(" Cell Detail", color=COLOR_ACCENT)
    dpg.add_separator()
    dpg.add_spacer(height=4)

    # Fixed-width value chip theme: gold text on a dark card, rounded frame.
    with dpg.theme() as _plain_text_theme:
        with dpg.theme_component(dpg.mvInputText):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg,        [0, 0, 0, 0])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [0, 0, 0, 0])
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive,  [0, 0, 0, 0])
            dpg.add_theme_color(dpg.mvThemeCol_Text,           COLOR_TEXT_DIM)
            dpg.add_theme_color(dpg.mvThemeCol_Border,         [0, 0, 0, 0])
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding,   0, 3)

    with dpg.theme() as _chip_theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button,        COLOR_CHORD_BG)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, COLOR_CHORD_BG)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  COLOR_CHORD_BG)
            dpg.add_theme_color(dpg.mvThemeCol_Text,          [255, 210, 50, 255])
            dpg.add_theme_color(dpg.mvThemeCol_Border,        [65, 65, 88, 255])
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding,    4)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding,     6, 3)
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign,  0.5, 0.5)

    def _chip(tag, default, width):
        dpg.add_button(tag=tag, label=default, width=width, height=22)
        dpg.bind_item_theme(tag, _chip_theme)

    with dpg.group(tag="prog_cell_detail_group", show=True):
        dpg.add_text("None", tag="prog_detail_pos", show=False)

        piano_pad = 20

        with dpg.group(horizontal=True):
            dpg.add_spacer(width=piano_pad)
            dpg.add_text("Root", color=COLOR_TEXT_DIM)
            dpg.add_spacer(width=16)
            dpg.add_button(label="\u25c0", width=25, height=22,
                           tag="prog_root_prev_btn",
                           callback=on_prog_cell_root_prev)
            _chip("prog_detail_root", "C", 38)
            dpg.add_button(label="\u25b6", width=25, height=22,
                           tag="prog_root_next_btn",
                           callback=on_prog_cell_root_next)
            dpg.add_spacer(width=20)
            dpg.add_text("Quality", color=COLOR_TEXT_DIM)
            dpg.add_spacer(width=4)
            dpg.add_button(label="\u25c0", width=25, height=22,
                           tag="prog_quality_prev_btn",
                           callback=on_prog_cell_quality_prev)
            _chip("prog_detail_quality", "Major", 66)
            dpg.add_button(label="\u25b6", width=25, height=22,
                           tag="prog_quality_next_btn",
                           callback=on_prog_cell_quality_next)
            dpg.add_spacer(width=16)
            dpg.add_text("Inv", color=COLOR_TEXT_DIM)
            dpg.add_spacer(width=4)
            dpg.add_button(label="\u25c0", width=25, height=22,
                           tag="prog_inv_prev_btn",
                           callback=on_prog_cell_inversion_prev)
            _chip("prog_detail_inversion", "Root", 46)
            dpg.add_button(label="\u25b6", width=25, height=22,
                           tag="prog_inv_next_btn",
                           callback=on_prog_cell_inversion_next)
            dpg.add_spacer(width=16)
            dpg.add_text("Oct", color=COLOR_TEXT_DIM)
            dpg.add_spacer(width=4)
            dpg.add_button(label="\u25c0", width=25, height=22,
                           tag="prog_octave_prev_btn",
                           callback=on_prog_cell_octave_prev)
            _chip("prog_detail_octave", "3", 30)
            dpg.add_button(label="\u25b6", width=25, height=22,
                           tag="prog_octave_next_btn",
                           callback=on_prog_cell_octave_next)

        dpg.add_spacer(height=4)

        with dpg.group(horizontal=True):
            dpg.add_spacer(width=piano_pad)
            dpg.add_text("Notes", color=COLOR_TEXT_DIM)
            dpg.add_spacer(width=4)
            _chip("prog_detail_notes", "--", 108)
            dpg.add_spacer(width=12)
            dpg.add_input_text(tag="prog_detail_inv_name", default_value="",
                               readonly=True, width=260, no_horizontal_scroll=True)
            dpg.bind_item_theme("prog_detail_inv_name", _plain_text_theme)


        # ── Multi-octave piano for cell detail (centered) ─────────────────
        dpg.add_spacer(height=8)

        with dpg.group(horizontal=True):
            dpg.add_spacer(width=piano_pad)
            with dpg.drawlist(tag="prog_piano_canvas",
                              width=PROG_PIANO_CANVAS_W,
                              height=PROG_PIANO_CANVAS_H):
                pass


def _build_sound_tab():
    """Sound settings."""
    with dpg.child_window(tag="sound_panel", width=-1,
                          height=-1, border=False):
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
            sound_cfg = get_sound_settings()
            dpg.add_combo(items=WAVE_DISPLAY_NAMES,
                          default_value=WAVE_INTERNAL_TO_DISPLAY.get(sound_cfg["mode"], "Triangle"),
                          tag="sound_mode_combo", width=120,
                          callback=on_wave_type_change)

        dpg.add_spacer(height=10)

        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_text("Audio Device:")
            dpg.add_spacer(width=4)
            from klo_chords.audio.sound import get_audio_devices, get_device_name
            devices = get_audio_devices()
            device_names = [d["name"] for d in devices]
            saved_device = get_device_name()
            # Resolve saved device name to a display name (fall back to System Default if not found)
            default_device = "System Default"
            if saved_device != "system_default" and saved_device in device_names:
                default_device = saved_device
            dpg.add_combo(items=device_names,
                          default_value=default_device,
                          tag="sound_device_combo", width=180,
                          callback=on_audio_device_change)
            dpg.add_spacer(width=8)
            dpg.add_text("Audio Quality:")
            dpg.add_spacer(width=4)
            quality_display = {"smooth": "Smooth", "responsive": "Responsive", "legacy": "Legacy"}
            sound_cfg2 = get_sound_settings()
            dpg.add_combo(items=["Smooth", "Responsive", "Legacy"],
                          default_value=quality_display.get(sound_cfg2.get("audio_quality", "smooth"), "Smooth"),
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

        dpg.add_spacer(height=12)
        dpg.add_text("Display", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_checkbox(label="Use jazz chord symbols (− △ ø)",
                             tag="use_jazz_symbols_toggle",
                             default_value=get_use_jazz_symbols(),
                             callback=on_jazz_symbols_toggle)
        dpg.add_spacer(height=6)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_text("Replaces 'min' with −, 'maj7' with △7, 'm7b5' with ø.",
                         color=COLOR_TEXT_DIM)

        dpg.add_spacer(height=20)
        dpg.add_text("Reset", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=8)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=16)
            dpg.add_button(label="Delete Saved Preferences",
                           tag="reset_prefs_btn", width=200, height=28,
                           callback=on_reset_prefs)
            with dpg.theme() as _danger_theme:
                with dpg.theme_component(dpg.mvButton):
                    dpg.add_theme_color(dpg.mvThemeCol_Button,        [120, 30, 30, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered,  [160, 40, 40, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,   [90, 20, 20, 255])
                    dpg.add_theme_color(dpg.mvThemeCol_Text,           [255, 100, 100, 255])
                    dpg.add_theme_style(dpg.mvStyleVar_FrameRounding,  4)
            dpg.bind_item_theme("reset_prefs_btn", _danger_theme)
            dpg.add_spacer(width=12)
            dpg.add_text("Resets all settings to defaults. Current session will also reset.",
                         color=COLOR_TEXT_DIM, wrap=300)


def build_ui():
    dpg.create_context()
    dpg.configure_app()

    _font_px = int(16 * _DISPLAY_SCALE)
    # draw_text sizes go up to 24px; bake the draw font at ≥24px to avoid upscaling.
    # On Mac _font_px=32 already exceeds 24, so reuse it; on Windows bake separately.
    _draw_px = max(_font_px, 24)

    with dpg.font_registry():
        path = font_path()
        fallback = font_path_fallback()
        _default_font = None
        if os.path.exists(path):
            _default_font = dpg.add_font(path, _font_px)
            _draw_fnt = dpg.add_font(path, _draw_px) if _draw_px != _font_px else _default_font
            set_draw_font(_draw_fnt)
        elif os.path.exists(fallback):
            _default_font = dpg.add_font(fallback, _font_px)
            _draw_fnt = dpg.add_font(fallback, _draw_px) if _draw_px != _font_px else _default_font
            set_draw_font(_draw_fnt)

    with dpg.window(tag="main_win", no_close=True, no_collapse=True,
                    no_scrollbar=True, width=-1, height=-1):

        # ── Shared toolbar (visible on every page) ──────────────────────────
        dpg.add_spacer(height=4)
        _build_toolbar()
        dpg.add_separator()
        dpg.add_spacer(height=6)

        with dpg.tab_bar(tag="main_tab_bar",
                         callback=on_tab_change):
            with dpg.tab(label="   Chords    ", tag="tab_chords"):
                _build_chord_tab()

            with dpg.tab(label=" Progression ", tag="tab_progression"):
                _build_progression_tab()

            with dpg.tab(label="    MIDI     ", tag="tab_midi"):
                midi_tab.build_midi_tab()

            with dpg.tab(label="  Settings   ", tag="tab_sound"):
                _build_sound_tab()

    # ── Theme ──────────────────────────────────────────────────────────────────
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 6, 6)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 4, 4)

    dpg.bind_theme(global_theme)

    with dpg.theme() as _tab_theme:
        with dpg.theme_component(dpg.mvTab):
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 14, 5)
    dpg.bind_item_theme("main_tab_bar", _tab_theme)

    # ── Viewport ────────────────────────────────────────────────────────────────
    dpg.create_viewport(title="KLO Chords", width=VIEWPORT_WIDTH,
                        height=VIEWPORT_HEIGHT, resizable=False,
                        decorated=True)
    ico = icon_path()
    if os.path.exists(ico):
        dpg.set_viewport_large_icon(ico)
        dpg.set_viewport_small_icon(ico)
    dpg.setup_dearpygui()
    if _default_font is not None:
        dpg.bind_font(_default_font)
    if _DISPLAY_SCALE != 1.0:
        dpg.set_global_font_scale(1.0 / _DISPLAY_SCALE)
    dpg.set_primary_window("main_win", True)
    dpg.show_viewport()

    # Apply keybind tab labels on boot if the preference was already set
    from klo_chords.state import _update_tab_labels
    _update_tab_labels()

    def _btn_theme(r, g, b):
        """Create a styled button theme: colored bg, white text, rounded."""
        with dpg.theme() as t:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,        [r,   g,   b,   255])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [min(r+30,255), min(g+30,255), min(b+30,255), 255])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  [max(r-30,0),   max(g-30,0),   max(b-30,0),   255])
                dpg.add_theme_color(dpg.mvThemeCol_Text,          [255, 255, 255, 255])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
        return t

    for tag, (r, g, b) in [
        ("prog_fill_btn",   (50,  120, 200)),   # blue
        ("prog_clear_btn",  (180, 50,  50)),    # red
        ("prog_export_btn", (60,  130, 80)),    # green
        ("prog_import_btn", (200, 160, 50)),    # yellow
    ]:
        if dpg.does_item_exist(tag):
            dpg.bind_item_theme(tag, _btn_theme(r, g, b))

    # ── Initialize ──────────────────────────────────────────────────────────────
    midi_tab.init()
    build_piano_keys("piano_canvas")
    build_multi_octave_piano("prog_piano_canvas")
    _refresh_chords()
    _refresh_progression()

    # ── Keyboard handlers ──────────────────────────────────────────────────────
    with dpg.handler_registry(tag="main_handler_registry"):
        # Row 0 (cells 0-7): keys 1-8, then QWERTY rows for cells 8-31
        PROG_KEY_CELL_MAP = [
            # Row 0: 1-8
            (dpg.mvKey_1, 0), (dpg.mvKey_2, 1), (dpg.mvKey_3, 2),
            (dpg.mvKey_4, 3), (dpg.mvKey_5, 4), (dpg.mvKey_6, 5),
            (dpg.mvKey_7, 6), (dpg.mvKey_8, 7),
            # Row 1: Q W E R T Y U I
            (dpg.mvKey_Q, 8), (dpg.mvKey_W, 9), (dpg.mvKey_E, 10),
            (dpg.mvKey_R, 11), (dpg.mvKey_T, 12), (dpg.mvKey_Y, 13),
            (dpg.mvKey_U, 14), (dpg.mvKey_I, 15),
            # Row 2: A S D F G H J K
            (dpg.mvKey_A, 16), (dpg.mvKey_S, 17), (dpg.mvKey_D, 18),
            (dpg.mvKey_F, 19), (dpg.mvKey_G, 20), (dpg.mvKey_H, 21),
            (dpg.mvKey_J, 22), (dpg.mvKey_K, 23),
            # Row 3: Z X C V B N M ,
            (dpg.mvKey_Z, 24), (dpg.mvKey_X, 25), (dpg.mvKey_C, 26),
            (dpg.mvKey_V, 27), (dpg.mvKey_B, 28), (dpg.mvKey_N, 29),
            (dpg.mvKey_M, 30), (dpg.mvKey_Comma, 31),
        ]
        for key, cell_idx in PROG_KEY_CELL_MAP:
            dpg.add_key_press_handler(key=key, callback=on_key_press, user_data=cell_idx)
        # Alt+1 = original suggestion card (Alt+~ intercepted by macOS, not doable cross-platform)
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
        # Cmd/Ctrl+1-4 = switch tabs
        _TAB_KEYS = [
            (dpg.mvKey_1, "tab_chords"),
            (dpg.mvKey_2, "tab_progression"),
            (dpg.mvKey_3, "tab_midi"),
            (dpg.mvKey_4, "tab_sound"),
        ]
        for key, tab_tag in _TAB_KEYS:
            dpg.add_key_press_handler(key=key, callback=_on_tab_shortcut, user_data=tab_tag)
        # Delete key — mvKey_Delete is Forward Delete; mvKey_Back is the main Delete key on macOS
        dpg.add_key_press_handler(key=dpg.mvKey_Delete, callback=on_prog_delete_selection)
        dpg.add_key_press_handler(key=dpg.mvKey_Back, callback=on_prog_delete_selection)


    from klo_chords.widgets import dpg_keyboard
    dpg_keyboard.setup()

    # ── Main loop ──────────────────────────────────────────────────────────────
    while dpg.is_dearpygui_running():
        dpg_keyboard.poll()
        _refresh_speaker_indicators()
        midi_tab.drain_ui_events()
        dpg.render_dearpygui_frame()

    midi_tab.cleanup()
    dpg.destroy_context()


# ── Keyboard shortcut helpers ────────────────────────────────────────────────────


def _on_tab_shortcut(sender, app_data, user_data):
    from klo_chords.widgets import dpg_keyboard
    if not dpg_keyboard.toggle_is_down():
        return
    dpg.set_value("main_tab_bar", user_data)
    on_tab_change(None, user_data)


def _on_key_with_ctrl(sender, app_data, user_data):
    """Handle key presses that require platform-native modifier (Ctrl on Win, Cmd on Mac)."""
    from klo_chords.widgets import dpg_keyboard
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
    from klo_chords.audio.sound import (
        set_volume, set_enabled, set_mode,
        set_audio_quality, set_legato, set_playback_mode,
        set_random_velocity, set_velocity_range, set_base_octave,
        set_sub_oscillator,
        get_audio_devices, set_device,
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
    set_sub_oscillator(prefs_data.get("sub_oscillator", False))
    init_show_keybinds(prefs_data.get("show_keybinds", True))
    init_use_jazz_symbols(prefs_data.get("use_jazz_symbols", False))
    # Apply saved audio device
    saved_device = prefs_data.get("audio_device", "system_default")
    if saved_device != "system_default":
        devices = get_audio_devices()
        for dev in devices:
            if dev["name"] == saved_device:
                set_device(dev["index"])
                break


if __name__ == "__main__":
    main()

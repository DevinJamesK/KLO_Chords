"""
KLO Chords - Application entry point.

Builds the Dear PyGui window layout and runs the event loop.
All logic (rendering, callbacks, state) lives in sibling modules.
"""

import dearpygui.dearpygui as dpg
import os

from klo_chords.chords import NOTE_NAMES, SCALE_TYPES
from klo_chords.theme import (
    COLOR_ACCENT, COLOR_BG_LIGHT, COLOR_TEXT_DIM, COLOR_TEXT,
    COLOR_CHORD_BG, COLOR_CHORD_BORDER,
    font_path, icon_path,
)
from klo_chords.piano import (
    build_piano_keys, PIANO_CANVAS_W, PIANO_CANVAS_H,
)
from klo_chords.state import (
    on_key_change, on_scale_change, on_sevenths_toggle,
    on_next_voicing, on_prev_voicing, on_key_press,
    on_prog_key_change, on_prog_scale_change, on_prog_sevenths_toggle,
    on_prog_fill, on_prog_slot_click,
    on_sound_enable_toggle, on_sound_mode_change,
    on_random_velocity_toggle, on_vel_min_change, on_vel_max_change,
    on_base_octave_change, on_playback_mode_change,
    on_legato_toggle, on_volume_change,
    on_wave_type_change,
    _refresh_chords, _refresh_progression, _refresh_speaker_indicators,
)
from klo_chords.sound import get_settings as get_sound_settings
from klo_chords.quality import quality_symbol

SCALE_NAMES = list(SCALE_TYPES.keys())

VIEWPORT_WIDTH  = 780
VIEWPORT_HEIGHT = 1080


def _build_toolbar():
    """Shared toolbar — called once, at the top of the window."""
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=8)
        dpg.add_text("Volume", color=COLOR_ACCENT)
        snd = get_sound_settings()
        dpg.add_slider_float(tag="volume_slider",
                              default_value=snd["volume"],
                              min_value=0.0, max_value=1.0,
                              width=120, callback=on_volume_change)
        dpg.add_spacer(width=20)
        dpg.add_text("Wave:", color=COLOR_ACCENT)
        dpg.add_combo(items=["triangle", "sine", "sawtooth"],
                      default_value=snd["mode"],
                      tag="toolbar_wave_combo", width=110,
                      callback=on_wave_type_change)
        dpg.add_spacer(width=20)
        dpg.add_text("Legato", color=COLOR_ACCENT)
        snd2 = get_sound_settings()
        dpg.add_checkbox(label="", tag="toolbar_legato_toggle",
                          default_value=True,
                          callback=on_legato_toggle)


def _build_chord_tab():
    """Main chord theory view."""
    with dpg.group(horizontal=True):

        # ── Left panel ────────────────────────────────────────────────────────
        with dpg.child_window(tag="left_panel", width=340,
                              height=-1, border=True):
            dpg.add_text("Key & Scale", color=COLOR_ACCENT)
            dpg.add_separator()
            dpg.add_spacer(height=4)

            with dpg.group(horizontal=True):
                dpg.add_text("Key  ")
                dpg.add_combo(items=NOTE_NAMES, default_value="C",
                              tag="key_combo", width=100,
                              callback=on_key_change)
                dpg.add_spacer(width=10)
                dpg.add_text("Scale")
                dpg.add_combo(items=SCALE_NAMES, default_value="Major",
                              tag="scale_combo", width=130,
                              callback=on_scale_change)

            dpg.add_spacer(height=4)
            dpg.add_checkbox(label="Include 7th chords",
                             tag="sevenths_toggle", default_value=False,
                             callback=on_sevenths_toggle)

            dpg.add_spacer(height=8)
            dpg.add_text("Scale Notes", color=COLOR_ACCENT)
            dpg.add_separator()
            dpg.add_spacer(height=2)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=22)
                dpg.add_text("C  |  D  |  E  |  F  |  G  |  A  |  B",
                             tag="scale_notes_text", color=COLOR_TEXT_DIM)

            dpg.add_spacer(height=7)
            dpg.add_text("Diatonic Chords", color=COLOR_ACCENT)
            dpg.add_separator()
            dpg.add_spacer(height=4)

            with dpg.group(tag="chord_list_scroll"):
                dpg.add_spacer(height=10)

            # Hint about number keys — expanded
            dpg.add_spacer(height=4)
            dpg.add_text("Press 1-8 to select chords.", color=COLOR_TEXT_DIM)
            dpg.add_text("Same chord again = stop sound.", color=COLOR_TEXT_DIM)

        # ── Right panel ──────────────────────────────────────────────────────
        with dpg.child_window(tag="right_panel", width=-1,
                              height=-1, border=True):
            dpg.add_text("Chord Detail", color=COLOR_ACCENT)
            dpg.add_separator()
            dpg.add_spacer(height=6)

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=24)
                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_text("Degree / Root:", color=COLOR_TEXT_DIM)
                        dpg.add_text("--", tag="detail_root", color=COLOR_ACCENT)
                    dpg.add_spacer(height=4)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Quality:", color=COLOR_TEXT_DIM)
                        dpg.add_text("--", tag="detail_quality",
                                     color=COLOR_ACCENT)
                    dpg.add_spacer(height=4)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Notes:", color=COLOR_TEXT_DIM)
                        dpg.add_text("--", tag="detail_notes", color=COLOR_ACCENT)
                    dpg.add_spacer(height=4)

                    with dpg.group(horizontal=True):
                        dpg.add_text("Intervals:", color=COLOR_TEXT_DIM)
                        dpg.add_text("--", tag="detail_intervals",
                                     color=COLOR_TEXT_DIM)
                    dpg.add_spacer(height=10)

            dpg.add_text("Fretboard", color=COLOR_ACCENT)
            dpg.add_separator()
            dpg.add_spacer(height=2)
            dpg.add_spacer(height=4)

            with dpg.drawlist(width=400, height=220,
                              tag="fretboard_canvas"):
                dpg.draw_rectangle([0, 0], [400, 220],
                                   fill=COLOR_BG_LIGHT,
                                   color=COLOR_BG_LIGHT,
                                   tag="fretboard_bg")

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=24)
                with dpg.group():
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="<  Prev", width=80,
                                       callback=on_prev_voicing)
                        dpg.add_text("", tag="voicing_label",
                                     color=COLOR_TEXT_DIM)
                        dpg.add_button(label="Next  >", width=80,
                                       callback=on_next_voicing)

            dpg.add_spacer(height=10)
            dpg.add_text("Keyboard", color=COLOR_ACCENT)
            dpg.add_separator()
            dpg.add_spacer(height=6)

            with dpg.group(horizontal=True):
                dpg.add_spacer(width=24)
                with dpg.drawlist(tag="piano_canvas",
                                  width=PIANO_CANVAS_W,
                                  height=PIANO_CANVAS_H):
                    pass

            # Inversion display — shows which notes are sounding
            dpg.add_spacer(height=6)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=24)
                dpg.add_text("", tag="detail_inversion",
                             color=COLOR_TEXT)
                dpg.add_spacer(width=10)
                dpg.add_text("", tag="detail_sounding_notes",
                             color=COLOR_TEXT_DIM)


def _build_progression_tab():
    """Chord progression tab with 8 large horizontal chord slots."""
    with dpg.group(horizontal=True):
        # ── Scale chooser ────────────────────────────────────────────────────
        with dpg.group():
            dpg.add_text("Key & Scale", color=COLOR_ACCENT)
            dpg.add_separator()
            dpg.add_spacer(height=4)

            with dpg.group(horizontal=True):
                dpg.add_text("Key  ")
                dpg.add_combo(items=NOTE_NAMES, default_value="C",
                              tag="prog_key_combo", width=100,
                              callback=on_prog_key_change)
                dpg.add_spacer(width=10)
                dpg.add_text("Scale")
                dpg.add_combo(items=SCALE_NAMES, default_value="Major",
                              tag="prog_scale_combo", width=130,
                              callback=on_prog_scale_change)

            dpg.add_spacer(height=4)
            with dpg.group(horizontal=True):
                dpg.add_checkbox(label="Include 7th chords",
                                 tag="prog_sevenths_toggle",
                                 default_value=False,
                                 callback=on_prog_sevenths_toggle)
                dpg.add_spacer(width=20)
                dpg.add_button(label="Fill from scale", width=140,
                               tag="prog_fill_btn", callback=on_prog_fill)

    dpg.add_spacer(height=8)
    dpg.add_separator()
    dpg.add_spacer(height=6)
    dpg.add_text("Chord Palette (click to play)", color=COLOR_ACCENT)
    dpg.add_separator()
    dpg.add_spacer(height=8)

    # 8 chord slots in a horizontal scrollable area
    with dpg.group(tag="prog_palette", horizontal=True):
        pass


def _build_sound_tab():
    """Sound settings."""
    with dpg.child_window(tag="sound_panel", width=-1,
                          height=-1, border=True):
        dpg.add_text("Sound Settings", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=8)

        with dpg.group(horizontal=True):
            dpg.add_checkbox(label="Enable sound",
                             tag="sound_enable", default_value=True,
                             callback=on_sound_enable_toggle)
            dpg.add_spacer(width=10)
            dpg.add_text("Wave type:")
            snd = get_sound_settings()
            dpg.add_combo(items=["triangle", "sine", "sawtooth"],
                          default_value=snd["mode"],
                          tag="sound_mode_combo", width=120,
                          callback=on_sound_mode_change)

        dpg.add_spacer(height=10)
        dpg.add_text("Velocity", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=4)
        dpg.add_checkbox(label="Random velocity per note",
                         tag="random_vel", default_value=True,
                         callback=on_random_velocity_toggle)
        dpg.add_spacer(height=4)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_text("Min:")
            dpg.add_slider_int(tag="vel_min_slider",
                               default_value=60,
                               min_value=1, max_value=127,
                               width=200, callback=on_vel_min_change)
            dpg.add_spacer(width=20)
            dpg.add_text("Max:")
            dpg.add_slider_int(tag="vel_max_slider",
                               default_value=100,
                               min_value=1, max_value=127,
                               width=200, callback=on_vel_max_change)

        dpg.add_spacer(height=10)
        dpg.add_text("Playback Mode", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=4)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_combo(items=["Toggle/Latch", "One-Shot"],
                          default_value="Toggle/Latch",
                          tag="playback_mode_combo", width=140,
                          callback=on_playback_mode_change)
            dpg.add_spacer(width=10)
            dpg.add_text("Toggle=on/off per chord, One-Shot=~1s",
                         color=COLOR_TEXT_DIM)

        dpg.add_spacer(height=10)
        dpg.add_text("Base Octave", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=4)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=20)
            dpg.add_text("Lower")
            dpg.add_slider_int(tag="base_octave_slider",
                               default_value=3,
                               min_value=2, max_value=6,
                               width=300,
                               callback=on_base_octave_change)
            dpg.add_text("Higher")

        dpg.add_spacer(height=10)
        dpg.add_text("Legato Mode", color=COLOR_ACCENT)
        dpg.add_separator()
        dpg.add_spacer(height=4)
        dpg.add_checkbox(label="Hold shared notes when switching chords",
                          tag="sound_legato_toggle", default_value=True,
                          callback=on_legato_toggle)
        dpg.add_spacer(height=4)
        dpg.add_text("When enabled, notes common to both chords stay held,",
                      color=COLOR_TEXT_DIM)
        dpg.add_text("only the differing notes change. Smoother transitions.",
                      color=COLOR_TEXT_DIM)

        dpg.add_spacer(height=16)
        dpg.add_text("Sound plays automatically when you select a chord.",
                     color=COLOR_TEXT_DIM)


def build_ui():
    dpg.create_context()
    dpg.configure_app()

    with dpg.font_registry():
        path = font_path()
        if os.path.exists(path):
            dpg.add_font(path, 16)

    with dpg.window(tag="main_win", no_close=True, no_collapse=True,
                    no_move=True, no_resize=True, no_title_bar=True,
                    no_scrollbar=True, width=-1, height=-1):

        # ── Shared toolbar (visible on every page) ──────────────────────────
        _build_toolbar()
        dpg.add_spacer(height=4)
        dpg.add_separator()
        dpg.add_spacer(height=4)

        with dpg.tab_bar(tag="main_tab_bar"):

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
                        height=VIEWPORT_HEIGHT, resizable=False)
    ico = icon_path()
    if os.path.exists(ico):
        dpg.set_viewport_large_icon(ico)
        dpg.set_viewport_small_icon(ico)
    dpg.setup_dearpygui()
    dpg.set_primary_window("main_win", True)
    dpg.show_viewport()

    # ── Initialize ──────────────────────────────────────────────────────────────
    build_piano_keys("piano_canvas")
    _refresh_chords()
    _refresh_progression()

    # ── Keyboard handler (number keys 1-8) ────────────────────────────────────
    with dpg.handler_registry():
        dpg.add_key_press_handler(key=dpg.mvKey_1, callback=on_key_press, user_data=0)
        dpg.add_key_press_handler(key=dpg.mvKey_2, callback=on_key_press, user_data=1)
        dpg.add_key_press_handler(key=dpg.mvKey_3, callback=on_key_press, user_data=2)
        dpg.add_key_press_handler(key=dpg.mvKey_4, callback=on_key_press, user_data=3)
        dpg.add_key_press_handler(key=dpg.mvKey_5, callback=on_key_press, user_data=4)
        dpg.add_key_press_handler(key=dpg.mvKey_6, callback=on_key_press, user_data=5)
        dpg.add_key_press_handler(key=dpg.mvKey_7, callback=on_key_press, user_data=6)
        dpg.add_key_press_handler(key=dpg.mvKey_8, callback=on_key_press, user_data=7)

    # ── Main loop ──────────────────────────────────────────────────────────────
    while dpg.is_dearpygui_running():
        _refresh_speaker_indicators()
        dpg.render_dearpygui_frame()

    dpg.destroy_context()


def main():
    try:
        build_ui()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()

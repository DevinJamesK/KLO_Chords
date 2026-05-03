"""
KLO Chords - Application entry point.

Builds the Dear PyGui window layout and runs the event loop.
All logic (rendering, callbacks, state) lives in sibling modules.
"""

import dearpygui.dearpygui as dpg
import os

from klo_chords.chords import NOTE_NAMES, SCALE_TYPES
from klo_chords.theme import (
    COLOR_ACCENT, COLOR_BG_LIGHT, COLOR_TEXT_DIM,
    font_path, icon_path,
)
from klo_chords.piano import (
    build_piano_keys, PIANO_CANVAS_W, PIANO_CANVAS_H,
)
from klo_chords.state import (
    on_key_change, on_scale_change, on_sevenths_toggle,
    on_next_voicing, on_prev_voicing,
    _refresh_chords,
)

SCALE_NAMES = list(SCALE_TYPES.keys())


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

        with dpg.group(horizontal=True):

            # ── Left panel ───────────────────────────────────────────────────
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

            # ── Right panel ──────────────────────────────────────────────────
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

    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 6, 6)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 4, 4)

    dpg.bind_theme(global_theme)
    dpg.create_viewport(title="KLO Chords", width=780,
                        height=950, resizable=False)
    ico = icon_path()
    if os.path.exists(ico):
        dpg.set_viewport_large_icon(ico)
        dpg.set_viewport_small_icon(ico)
    dpg.setup_dearpygui()
    dpg.set_primary_window("main_win", True)
    dpg.show_viewport()

    build_piano_keys("piano_canvas")
    _refresh_chords()

    while dpg.is_dearpygui_running():
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

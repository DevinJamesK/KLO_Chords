"""
Cross-platform modifier key polling helper for Dear PyGui.

Dear PyGui's key press handlers fire per-key and do not provide reliable
modifier key state. This module uses DPG's built-in is_key_down() to poll
the Ctrl and Shift keys on each frame, providing simple ctrl_is_down()
and shift_is_down() checks that work on Windows, macOS, and Linux.

Usage in build_ui():
    from klo_chords import dpg_keyboard
    dpg_keyboard.setup()
    # ... then in the main loop:
    while dpg.is_dearpygui_running():
        dpg_keyboard.poll()
        ...
"""

import dearpygui.dearpygui as dpg

_ctrl_held  = False
_shift_held = False


def ctrl_is_down() -> bool:
    """Return True if either Ctrl key is currently held."""
    return _ctrl_held


def shift_is_down() -> bool:
    """Return True if Shift key is currently held."""
    return _shift_held


def setup():
    """Initialize the keyboard state tracker."""
    pass


def poll():
    """Call once per frame to update modifier key state via DPG's is_key_down()."""
    global _ctrl_held, _shift_held
    _ctrl_held  = dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl)
    _shift_held = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)

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
import sys

_ctrl_held  = False
_shift_held = False
_super_held = False

# ── GLFW raw key codes (reliable fallback when named constants differ) ───────────
# GLFW_KEY_LEFT_SUPER  = 343  (Command on macOS, Windows key on Windows/Linux)
# GLFW_KEY_RIGHT_SUPER = 347
_KEY_LSUPER = getattr(dpg, 'mvKey_LWin',
              getattr(dpg, 'mvKey_LeftSuper',
              343))
_KEY_RSUPER = getattr(dpg, 'mvKey_RWin',
              getattr(dpg, 'mvKey_RightSuper',
              347))


def ctrl_is_down() -> bool:
    """Return True if either Ctrl key is currently held."""
    return _ctrl_held


def cmd_is_down() -> bool:
    """Return True if the Super/Command key (macOS Cmd, Windows key) is held."""
    return _super_held


def shift_is_down() -> bool:
    """Return True if Shift key is currently held."""
    return _shift_held


def mod_is_down() -> bool:
    """Return True if either Ctrl (Windows/Linux) or Cmd (macOS) is held.

    Use this for cross-platform modifier+click operations (e.g. toggle selection).
    """
    return _ctrl_held or _super_held


def toggle_is_down() -> bool:
    """Return True if the *platform-native* toggle modifier is held.

    - macOS  → Command (⌘)   —  Ctrl is right-click on Mac, so we ignore it.
    - Windows / Linux → Ctrl —  Super/Win key is not used for selection.
    """
    if sys.platform == 'darwin':
        return _super_held
    return _ctrl_held


def _on_super_press(sender=None, app_data=None):
    """Key-press handler for Super/Cmd key — sets state immediately."""
    global _super_held
    _super_held = True


def _on_super_release(sender=None, app_data=None):
    """Key-release handler for Super/Cmd key — clears state immediately."""
    global _super_held
    _super_held = False


def setup():
    """Initialize the keyboard state tracker.

    Registers key press/release handlers for the Super/Command key so its
    state is tracked reliably on all platforms (especially macOS, where
    is_key_down() may not report the Command key correctly).
    """
    with dpg.handler_registry():
        dpg.add_key_press_handler(key=_KEY_LSUPER, callback=_on_super_press)
        dpg.add_key_release_handler(key=_KEY_LSUPER, callback=_on_super_release)
        dpg.add_key_press_handler(key=_KEY_RSUPER, callback=_on_super_press)
        dpg.add_key_release_handler(key=_KEY_RSUPER, callback=_on_super_release)


def poll():
    """Call once per frame to update modifier key state.

    (Not needed for Super/Cmd — that's tracked via press/release handlers
    registered in setup(). We still poll Ctrl/Shift for keyboard shortcut
    detection.)
    """
    global _ctrl_held, _shift_held, _super_held
    _ctrl_held  = dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl)
    _shift_held = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
    # Also poll Super key as a fallback in case press/release handlers don't fire
    # (e.g. if the platform uses a different key constant than we expected).
    # Only ever sets _super_held to True — release is handled by the handler.
    if dpg.is_key_down(_KEY_LSUPER) or dpg.is_key_down(_KEY_RSUPER):
        _super_held = True

"""
Cross-platform modifier key polling helper for Dear PyGui.

Dear PyGui's key press handlers fire per-key and do not provide reliable
modifier key state. This module uses DPG's built-in is_key_down() to poll
the Ctrl and Shift keys on each frame, providing simple ctrl_is_down()
and shift_is_down() checks that work on Windows, macOS, and Linux.

On macOS, the Command key uses DPG key codes 527 / 663 (not GLFW 343/347),
tracked via key press/release handlers since is_key_down() doesn't report it.
On Windows/Linux, the Super/Win key is not used.

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
_alt_held   = False

# ── macOS Command key codes (from DPG key handler, not GLFW) ─────────────────
# On macOS, DPG reports Cmd press as 527 and release as 663.
_KEY_CMD_PRESS   = 527
_KEY_CMD_RELEASE = 663


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


def alt_is_down() -> bool:
    """Return True if Alt/Option key is currently held."""
    return _alt_held


def toggle_is_down() -> bool:
    """Return True if the *platform-native* toggle modifier is held.

    - macOS  → Command (⌘)   —  Ctrl is right-click on Mac, so we ignore it.
    - Windows / Linux → Ctrl —  Super/Win key is not used for selection.
    """
    if sys.platform == 'darwin':
        return _super_held
    return _ctrl_held


def _on_cmd_press(sender=None, app_data=None):
    global _super_held
    _super_held = True


def _on_cmd_release(sender=None, app_data=None):
    global _super_held
    _super_held = False


def setup():
    """Initialize the keyboard state tracker.

    Registers DPG key press/release handlers for the macOS Command key
    (codes 527 press, 663 release — validated on macOS via test_keys.py).
    """
    with dpg.handler_registry():
        dpg.add_key_press_handler(key=_KEY_CMD_PRESS, callback=_on_cmd_press)
        dpg.add_key_release_handler(key=_KEY_CMD_RELEASE, callback=_on_cmd_release)


def poll():
    """Call once per frame to update Ctrl/Shift/Alt key state via DPG is_key_down()."""
    global _ctrl_held, _shift_held, _alt_held
    _ctrl_held  = dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl)
    _shift_held = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
    _alt_held   = dpg.is_key_down(dpg.mvKey_LAlt) or dpg.is_key_down(dpg.mvKey_RAlt)

"""
Cross-platform modifier key polling helper for Dear PyGui.

Dear PyGui's key press handlers fire per-key and do not provide reliable
modifier key state. This module uses DPG's built-in is_key_down() to poll
the Ctrl and Shift keys on each frame, providing simple ctrl_is_down()
and shift_is_down() checks that work on Windows, macOS, and Linux.

On macOS, the Command key uses DPG key codes 527 / 663 (not GLFW 343/347),
tracked via key press/release handlers since is_key_down() doesn't report it.
On Windows/Linux, the Super/Win key is not used.

On macOS, the Option/Alt key is also tracked via key press/release handlers
because is_key_down() does not report it reliably (same issue as Command).
On Windows/Linux, is_key_down() is used as before.

Usage in build_ui():
    from klo_chords.widgets import dpg_keyboard
    dpg_keyboard.setup()
    # ... then in the main loop:
    while dpg.is_dearpygui_running():
        dpg_keyboard.poll()
        ...
"""

from __future__ import annotations

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


def _on_alt_press(sender=None, app_data=None):
    global _alt_held
    _alt_held = True


def _on_alt_release(sender=None, app_data=None):
    global _alt_held
    _alt_held = False


def setup():
    """Initialize the keyboard state tracker.

    Registers DPG key press/release handlers for the macOS Command key
    (codes 527 press, 663 release — validated on macOS via test_keys.py).

    On macOS also registers press/release for Option/Alt using GLFW key
    codes (342 press, 346 release) because is_key_down() doesn't report
    it reliably.  If those codes don't fire, run utils/test_keys.py and
    update the constants below.
    """
    with dpg.handler_registry():
        dpg.add_key_press_handler(key=_KEY_CMD_PRESS, callback=_on_cmd_press)
        dpg.add_key_release_handler(key=_KEY_CMD_RELEASE, callback=_on_cmd_release)
        # On macOS, track Option/Alt via press/release handlers (same
        # limitation as Command: is_key_down() doesn't report it).
        if sys.platform == 'darwin':
            # Use GLFW key codes for Alt (342 = Left Alt / Option, 346 = Right).
            # If DPG reports different codes on your macOS version, run
            #   python3 utils/test_keys.py
            # press Option, note the code printed for [PRESS] / [RELEASE],
            # and update these constants.
            _KEY_ALT_PRESS   = getattr(dpg, 'mvKey_LAlt', 342)   # GLFW_KEY_LEFT_ALT
            _KEY_ALT_RELEASE = getattr(dpg, 'mvKey_RAlt', 346)   # GLFW_KEY_RIGHT_ALT
            dpg.add_key_press_handler(key=_KEY_ALT_PRESS, callback=_on_alt_press)
            dpg.add_key_release_handler(key=_KEY_ALT_PRESS, callback=_on_alt_release)
            dpg.add_key_press_handler(key=_KEY_ALT_RELEASE, callback=_on_alt_press)
            dpg.add_key_release_handler(key=_KEY_ALT_RELEASE, callback=_on_alt_release)


def poll():
    """Call once per frame to update Ctrl/Shift/Alt key state via DPG is_key_down().

    On macOS, Alt/Option state is tracked via press/release handlers (see setup())
    and is NOT polled here because is_key_down() doesn't report it reliably.
    """
    global _ctrl_held, _shift_held
    _ctrl_held  = dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl)
    _shift_held = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
    # On Windows/Linux, poll Alt via is_key_down().  On macOS, Alt is managed
    # by press/release handlers (see setup()).
    if sys.platform != 'darwin':
        global _alt_held
        _alt_held = dpg.is_key_down(dpg.mvKey_LAlt) or dpg.is_key_down(dpg.mvKey_RAlt)

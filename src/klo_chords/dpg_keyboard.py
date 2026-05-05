"""
Cross-platform modifier key polling helper for Dear PyGui.

Dear PyGui's key press handlers fire per-key and do not provide reliable
modifier key state. This module uses DPG's built-in is_key_down() to poll
the Ctrl and Shift keys on each frame, providing simple ctrl_is_down()
and shift_is_down() checks that work on Windows, macOS, and Linux.

On macOS, the Command key is detected via the native Carbon/CoreGraphics
CGEventSourceFlagsState() API, because DearPyGui (and GLFW) do not expose
the Cmd key state through is_key_down() or key press/release handlers.

Usage in build_ui():
    from klo_chords import dpg_keyboard
    dpg_keyboard.setup()
    # ... then in the main loop:
    while dpg.is_dearpygui_running():
        dpg_keyboard.poll()
        ...
"""

import ctypes
import dearpygui.dearpygui as dpg
import sys

_ctrl_held  = False
_shift_held = False
_super_held = False

# ── macOS Command-key detection via CoreGraphics ──────────────────────────────
# kCGEventFlagMaskCommand = 1 << 20  (NSEventModifierFlagCommand)
_kCGEventFlagMaskCommand = 1 << 20

# Cache the function pointer (we're on macOS, so Carbon/CoreGraphics is always available)
_CGEventSourceFlagsState = None
def _init_mac_cmd_detect():
    """Resolve the CGEventSourceFlagsState function once."""
    global _CGEventSourceFlagsState
    if _CGEventSourceFlagsState is None:
        try:
            cg = ctypes.cdll.LoadLibrary(
                '/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
            _CGEventSourceFlagsState = cg.CGEventSourceFlagsState
            _CGEventSourceFlagsState.restype = ctypes.c_uint64
            _CGEventSourceFlagsState.argtypes = [ctypes.c_int32]
        except Exception:
            _CGEventSourceFlagsState = False  # sentinel: not available


def _mac_cmd_is_down() -> bool:
    """Return True if the Command key is held (macOS only)."""
    global _CGEventSourceFlagsState
    if _CGEventSourceFlagsState is None:
        _init_mac_cmd_detect()
    if _CGEventSourceFlagsState is False:
        return False
    # kCGEventSourceStateCombinedSessionState = 0
    flags = _CGEventSourceFlagsState(0)
    return bool(flags & _kCGEventFlagMaskCommand)


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


def setup():
    """Initialize the keyboard state tracker.

    On macOS, pre-load the CoreGraphics framework for Cmd-key detection.
    No DPG handler registration needed — Cmd is detected via native API.
    """
    if sys.platform == 'darwin':
        _init_mac_cmd_detect()


def poll():
    """Call once per frame to update modifier key state using DPG and native APIs."""
    global _ctrl_held, _shift_held, _super_held
    _ctrl_held  = dpg.is_key_down(dpg.mvKey_LControl) or dpg.is_key_down(dpg.mvKey_RControl)
    _shift_held = dpg.is_key_down(dpg.mvKey_LShift) or dpg.is_key_down(dpg.mvKey_RShift)
    if sys.platform == 'darwin':
        _super_held = _mac_cmd_is_down()

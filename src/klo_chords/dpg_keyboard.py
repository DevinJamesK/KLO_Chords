"""
Win32-based modifier key polling helper for Dear PyGui.

Dear PyGui's key press handlers fire per-key and do not provide reliable
modifier key state. This module uses the Win32 API to poll the Ctrl and Shift
keys on each frame, providing simple ctrl_is_down() and shift_is_down() checks.

Usage in build_ui():
    from klo_chords import dpg_keyboard
    dpg_keyboard.setup()
    # ... then in the main loop:
    while dpg.is_dearpygui_running():
        dpg_keyboard.poll()
        ...
"""

import ctypes

# Win32 virtual-key codes
VK_SHIFT     = 0x10
VK_LCONTROL  = 0xA2
VK_RCONTROL  = 0xA3

user32 = ctypes.windll.user32

_ctrl_held  = False
_shift_held = False


def ctrl_is_down() -> bool:
    """Return True if either Ctrl key is currently held."""
    return _ctrl_held


def shift_is_down() -> bool:
    """Return True if Shift key is currently held."""
    return _shift_held


def setup():
    """Initialize the keyboard state tracker (no-op on Windows)."""
    pass


def poll():
    """Call once per frame to update modifier key state via Win32."""
    global _ctrl_held, _shift_held
    # GetAsyncKeyState — high bit (0x8000) = currently down
    lctrl = user32.GetAsyncKeyState(VK_LCONTROL) & 0x8000
    rctrl = user32.GetAsyncKeyState(VK_RCONTROL) & 0x8000
    _ctrl_held  = bool(lctrl or rctrl)
    _shift_held = bool(user32.GetAsyncKeyState(VK_SHIFT) & 0x8000)

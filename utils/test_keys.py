"""Diagnostic tool: print every key press, release, and modifier-key state.

Run with:  python3 utils/test_keys.py

Use this to discover:
  - What DPG key code the ` / ~ key sends on this platform
  - Whether is_key_down() works for Alt/Option on macOS
  - The correct DPG key codes for Option press/release on macOS
"""
import dearpygui.dearpygui as dpg
import sys

dpg.create_context()

# ------------------------------------------------------------------
# Look up a DPG key name from its integer code (best-effort)
# ------------------------------------------------------------------
_KEY_LOOKUP = {}
for _attr in dir(dpg):
    if _attr.startswith("mvKey_"):
        try:
            _KEY_LOOKUP[int(getattr(dpg, _attr))] = _attr
        except (TypeError, ValueError):
            pass


def _key_name(code):
    if isinstance(code, int) and code in _KEY_LOOKUP:
        return _KEY_LOOKUP[code]
    return f"<unknown: {code}>"


# ------------------------------------------------------------------
# Key press / release handlers (key=-1 catches every key)
# ------------------------------------------------------------------
def on_key_press(s, app_data, u):
    name = _key_name(app_data)
    print(f"[PRESS ]  code={app_data:>5d}  name={name}")


def on_key_release(s, app_data, u):
    name = _key_name(app_data)
    print(f"[RELEASE] code={app_data:>5d}  name={name}")


with dpg.handler_registry():
    dpg.add_key_press_handler(key=-1, callback=on_key_press, user_data="PRESS")
    dpg.add_key_release_handler(key=-1, callback=on_key_release, user_data="RELEASE")

# ------------------------------------------------------------------
# Per-frame modifier polling
# ------------------------------------------------------------------
# Key codes — standard GLFW values, but DPG may report different ones on macOS.
MOD_KEYS = {
    "LControl": dpg.mvKey_LControl,
    "RControl": dpg.mvKey_RControl,
    "LShift":   dpg.mvKey_LShift,
    "RShift":   dpg.mvKey_RShift,
    "LAlt":     dpg.mvKey_LAlt,      # Option on macOS
    "RAlt":     dpg.mvKey_RAlt,
    # These may *not* work on macOS (DPG reports Cmd as 527/663 instead of
    # GLFW 343/347), but poll them anyway.
    "LSuper":   343 if "mvKey_LSuper" not in dir(dpg) else dpg.mvKey_LSuper,
    "RSuper":   347 if "mvKey_RSuper" not in dir(dpg) else dpg.mvKey_RSuper,
}

# Try DPG's own constants first, fall back to raw GLFW codes
try:
    MOD_KEYS["LSuper"] = dpg.mvKey_LSuper
except AttributeError:
    pass
try:
    MOD_KEYS["RSuper"] = dpg.mvKey_RSuper
except AttributeError:
    pass

_prev_state = {}


def poll_modifiers():
    global _prev_state
    changed = False
    for label, code in MOD_KEYS.items():
        down = dpg.is_key_down(code)
        if label not in _prev_state or _prev_state[label] != down:
            _prev_state[label] = down
            changed = True
            state = "DOWN" if down else "up  "
            print(f"[MOD]  {label:12s}  {state}  (is_key_down(code={code}))")
    return changed


# ------------------------------------------------------------------
# UI
# ------------------------------------------------------------------
_PLATFORM = sys.platform
with dpg.window(label="Key Diagnostic", width=600, height=320):
    dpg.add_text(f"Platform: {_PLATFORM}")
    dpg.add_spacer(height=8)
    dpg.add_text("Instructions:", color=[80, 200, 120])
    dpg.add_text("  1. Press the ` / ~ key alone and watch the terminal.")
    dpg.add_text("  2. Press Alt+`,  Shift+`,  Cmd+`  on macOS.")
    dpg.add_text("  3. Watch both [PRESS] events and [MOD] lines.")
    dpg.add_spacer(height=8)
    dpg.add_text("Key codes to look for:", color=[200, 180, 60])
    dpg.add_text(f"  mvKey_Tilde     = {dpg.mvKey_Tilde}", color=[200, 180, 60])
    dpg.add_text(f"  mvKey_LAlt      = {dpg.mvKey_LAlt}", color=[200, 180, 60])
    dpg.add_text(f"  mvKey_RAlt      = {dpg.mvKey_RAlt}", color=[200, 180, 60])
    dpg.add_text(f"  mvKey_LControl  = {dpg.mvKey_LControl}", color=[200, 180, 60])
    dpg.add_text(f"  mvKey_LShift    = {dpg.mvKey_LShift}", color=[200, 180, 60])
    dpg.add_spacer(height=8)
    dpg.add_text("On macOS, Option = Alt, Command = Super.", color=[140, 140, 160])
    dpg.add_text("DPG reports Cmd press as 527, release as 663.", color=[140, 140, 160])
    dpg.add_text("Option may use non-GLFW codes too.", color=[140, 140, 160])
    dpg.add_spacer(height=12)
    dpg.add_text("Press any key. Close window to exit.", color=[255, 120, 120])

dpg.create_viewport(title="Key Diagnostic", width=620, height=380)
dpg.setup_dearpygui()
dpg.show_viewport()

print("=" * 60)
print(f"KEY DIAGNOSTIC  |  Platform: {_PLATFORM}")
print("=" * 60)
print("mvKey_Tilde     =", dpg.mvKey_Tilde)
print("mvKey_LAlt      =", dpg.mvKey_LAlt)
print("mvKey_RAlt      =", dpg.mvKey_RAlt)
print("mvKey_LControl  =", dpg.mvKey_LControl)
print("mvKey_LShift    =", dpg.mvKey_LShift)
print("mvKey_LSuper    =", dpg.mvKey_LSuper if "mvKey_LSuper" in dir(dpg) else "N/A")
print("mvKey_RSuper    =", dpg.mvKey_RSuper if "mvKey_RSuper" in dir(dpg) else "N/A")
print()
print("Press the ` / ~ key now (with and without Alt/Option).")
print("Press Ctrl+C in terminal to force-quit, or close window.")
print()

_frame = 0
while dpg.is_dearpygui_running():
    _frame += 1
    # Poll modifiers every frame, print only on change
    changed = poll_modifiers()
    # Only print a dot every 120 frames (≈2s) if nothing changes,
    # so users know the loop runs and modifier state is stale.
    if not changed and _frame % 120 == 0:
        # print a compact summary every 2s
        parts = []
        for label in ("LAlt", "RAlt", "LShift", "RShift", "LControl", "RControl"):
            parts.append(f"{label}={_prev_state.get(label, '?')}")
        # print on one line (no newline so it's compact)
        pass  # keep terminal quiet unless something changes
    dpg.render_dearpygui_frame()

dpg.destroy_context()
print("Done.")

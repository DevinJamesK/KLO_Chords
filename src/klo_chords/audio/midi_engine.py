"""MIDI tab — ports, send note, piano visualizer, sync monitor, CC monitor, log."""

from __future__ import annotations

import queue
import threading
import time

import dearpygui.dearpygui as dpg

from klo_chords.rendering.theme import COLOR_ACCENT, COLOR_TEXT_DIM

try:
    import rtmidi as _rtmidi
    _RTMIDI_OK = True
except ImportError:
    _RTMIDI_OK = False

# ── MIDI protocol constants ────────────────────────────────────────────────────

NOTE_OFF          = 0x80
NOTE_ON           = 0x90
POLY_AT           = 0xA0
CONTROL_CHANGE    = 0xB0
PROGRAM_CHANGE    = 0xC0
CHAN_AT           = 0xD0
PITCH_BEND        = 0xE0
SYSTEM            = 0xF0

TIMING_CLOCK      = 0xF8
MIDI_START        = 0xFA
MIDI_CONTINUE     = 0xFB
MIDI_STOP         = 0xFC
SONG_POSITION     = 0xF2

MOD_WHEEL         = 1
SUSTAIN_CC        = 64
ALL_SOUND_OFF     = 120
ALL_NOTES_OFF     = 123

from klo_chords.core.chords import NOTE_NAMES as _NOTE_NAMES

CC_NAMES = {
    1:  "Mod",   7:  "Vol",   10: "Pan",  11: "Expr",
    64: "Sus",   65: "Port",  66: "Sost", 67: "Soft",
    71: "Res",   74: "Bright",91: "Rev",  93: "Cho",
    120:"SndOff",123:"NoteOff",
}

def _status_class(status):
    return SYSTEM if status >= SYSTEM else (status & 0xF0)

def _channel(status):
    return (status & 0x0F) if status < SYSTEM else None

def _note_name(n):
    return f"{_NOTE_NAMES[n % 12]}{(n // 12) - 1}"

# ── Piano geometry ─────────────────────────────────────────────────────────────

_WW, _WH  = 30, 84
_BW, _BH  = 19, 50
_WHITE_PC = [0, 2, 4, 5, 7, 9, 11]
_BLACK_PC = [1, 3, 6, 8, 10]
_BLACK_X  = [_WW - _BW//2, 2*_WW - _BW//2, 4*_WW - _BW//2,
             5*_WW - _BW//2, 6*_WW - _BW//2]
_PB_CENTER = 31
_PB_HALF   = 30

# ── Module state ───────────────────────────────────────────────────────────────

_driver         = None
_stop_polling   = threading.Event()
_ui_events: queue.Queue = queue.Queue()

# Piano
_active_pitches = {}   # pitch_class → (count, velocity)
_pitch_bend     = 8192
_mod_wheel      = 0

# Ports
_ins:  list = []
_outs: list = []

# Sync
_sync_clock_count      = 0
_sync_bpm              = 0.0
_sync_last_clock_time  = None
_sync_transport_state  = "Stopped"
_sync_song_position    = 0

_CHANNEL_OPTIONS = ["All"] + [str(i) for i in range(16)]

# Program Change state
_PC_MODES = ["GM", "Roland", "Yamaha"]
_pc_mode    = "GM"
_pc_bank_msb = 0
_pc_bank_lsb = 0
_pc_program  = 0


# ── MidiDriver ─────────────────────────────────────────────────────────────────

class MidiDriver:
    def __init__(self):
        self.midi_in  = _rtmidi.MidiIn()
        self.midi_in.ignore_types(sysex=False, timing=False, active_sense=False)
        self.midi_out = _rtmidi.MidiOut()
        self._in_port  = None
        self._out_port = None

    def list_ports(self):
        return self.midi_in.get_ports(), self.midi_out.get_ports()

    def open_input(self, port=0, callback=None):
        self.midi_in.open_port(port)
        if callback:
            self.midi_in.set_callback(callback)
        self._in_port = port

    def open_output(self, port=0):
        self.midi_out.open_port(port)
        self._out_port = port

    def send(self, message):
        self.midi_out.send_message(message)

    def note_on(self, note, vel=127, ch=0):
        self.send([NOTE_ON | ch, note, vel])

    def note_off(self, note, ch=0):
        self.send([NOTE_OFF | ch, note, 0])

    def send_cc(self, cc, val, ch=0):
        self.send([CONTROL_CHANGE | ch, cc, val])

    def stop_all(self, ch=0):
        self.send_cc(ALL_NOTES_OFF, 0, ch)
        self.send_cc(ALL_SOUND_OFF, 0, ch)

    def close(self):
        if self._in_port is not None:
            self.midi_in.close_port()
            self._in_port = None
        if self._out_port is not None:
            self.midi_out.close_port()
            self._out_port = None


# ── Init / cleanup ─────────────────────────────────────────────────────────────

def init():
    global _driver, _ins, _outs
    if not _RTMIDI_OK:
        return
    _driver = MidiDriver()
    _ins, _outs = _driver.list_ports()
    t = threading.Thread(target=_poll_ports, daemon=True)
    t.start()


def cleanup():
    _stop_polling.set()
    if _driver:
        if _driver._out_port is not None:
            for ch in range(16):
                _driver.stop_all(ch)
        _driver.close()


# ── Port management ─────────────────────────────────────────────────────────────

def _on_midi_in(message, _):
    _ui_events.put(("midi", message))


def _output_ready():
    if _driver and _driver._out_port is not None:
        return True
    _midi_log("SYS", "No output connected.")
    return False


def connect_input(*_):
    if not _driver:
        return
    name = dpg.get_value("midi_in_port")
    if name == "None":
        if _driver._in_port is not None:
            _driver.midi_in.close_port()
            _driver._in_port = None
            _midi_log("SYS", "Input disconnected.")
        return
    if _ins and name in _ins:
        idx = _ins.index(name)
        if _driver._in_port is not None:
            _driver.midi_in.close_port()
        _driver.open_input(idx, callback=_on_midi_in)
        _midi_log("SYS", f"Input connected: {name}")


def connect_output(*_):
    if not _driver:
        return
    name = dpg.get_value("midi_out_port")
    if name == "None":
        if _driver._out_port is not None:
            _driver.midi_out.close_port()
            _driver._out_port = None
            _reset_output_controls()
            _midi_log("SYS", "Output disconnected.")
        return
    if _outs and name in _outs:
        idx = _outs.index(name)
        if _driver._out_port is not None:
            _driver.midi_out.close_port()
        _driver.open_output(idx)
        _midi_log("SYS", f"Output connected: {name}")


def _reset_output_controls():
    pass


def _auto_connect():
    if not _driver or not dpg.does_item_exist("midi_auto_connect"):
        return
    if not dpg.get_value("midi_auto_connect"):
        return
    if len(_ins) == 1 and _driver._in_port is None:
        _driver.open_input(0, callback=_on_midi_in)
        dpg.configure_item("midi_in_port", items=["None"] + _ins, default_value=_ins[0])
        _midi_log("SYS", f"Auto-connected input: {_ins[0]}")
    if len(_outs) == 1 and _driver._out_port is None:
        _driver.open_output(0)
        dpg.configure_item("midi_out_port", items=["None"] + _outs, default_value=_outs[0])
        _midi_log("SYS", f"Auto-connected output: {_outs[0]}")


def _process_port_change(new_ins, new_outs):
    global _ins, _outs
    if _driver._in_port is not None:
        old = _ins[_driver._in_port] if _driver._in_port < len(_ins) else None
        if old not in new_ins:
            _driver.midi_in.close_port()
            _driver._in_port = None
            if dpg.does_item_exist("midi_in_port"):
                dpg.configure_item("midi_in_port", items=["None"], default_value="None")
            _midi_log("SYS", "Input disconnected.")
    if _driver._out_port is not None:
        old = _outs[_driver._out_port] if _driver._out_port < len(_outs) else None
        if old not in new_outs:
            _driver.midi_out.close_port()
            _driver._out_port = None
            _reset_output_controls()
            if dpg.does_item_exist("midi_out_port"):
                dpg.configure_item("midi_out_port", items=["None"], default_value="None")
            _midi_log("SYS", "Output disconnected.")
    _ins, _outs = new_ins, new_outs
    if dpg.does_item_exist("midi_in_port"):
        dpg.configure_item("midi_in_port", items=["None"] + _ins)
    if dpg.does_item_exist("midi_out_port"):
        dpg.configure_item("midi_out_port", items=["None"] + _outs)
    _auto_connect()


def _poll_ports():
    last_ins, last_outs = [], []
    while not _stop_polling.wait(1):
        try:
            new_ins  = _driver.midi_in.get_ports()
            new_outs = _driver.midi_out.get_ports()
            if new_ins != last_ins or new_outs != last_outs:
                last_ins, last_outs = new_ins, new_outs
                _ui_events.put(("ports", new_ins, new_outs))
        except Exception as e:
            _ui_events.put(("sys", f"Port poll error: {e}"))


# ── Piano display ──────────────────────────────────────────────────────────────

def _vel_color(vel):
    t = vel / 127.0
    return [int(60 + t * 195), int(140 - t * 100), int(255 - t * 215), 255]


def _update_piano_keys():
    for pc in _WHITE_PC:
        if pc in _active_pitches:
            fill = _vel_color(_active_pitches[pc][1])
        else:
            fill = [255, 255, 255, 255]
        if dpg.does_item_exist(f"midi_wkey_{pc}"):
            dpg.configure_item(f"midi_wkey_{pc}", fill=fill)
    for pc in _BLACK_PC:
        if pc in _active_pitches:
            fill = _vel_color(_active_pitches[pc][1])
        else:
            fill = [20, 20, 20, 255]
        if dpg.does_item_exist(f"midi_bkey_{pc}"):
            dpg.configure_item(f"midi_bkey_{pc}", fill=fill)


def _update_pitch_display(bend):
    if not dpg.does_item_exist("midi_pitch_fill"):
        return
    norm = (bend - 8192) / 8192.0
    fill_h = max(1, int(abs(norm) * _PB_HALF))
    if norm >= 0:
        dpg.configure_item("midi_pitch_fill",
                           pmin=[1, _PB_CENTER - fill_h], pmax=[20, _PB_CENTER])
    else:
        dpg.configure_item("midi_pitch_fill",
                           pmin=[1, _PB_CENTER], pmax=[20, _PB_CENTER + fill_h])


def _update_mod_display(mod):
    if not dpg.does_item_exist("midi_mod_fill"):
        return
    fill_h = max(1, int((mod / 127) * 62))
    dpg.configure_item("midi_mod_fill", pmin=[1, 63 - fill_h], pmax=[20, 63])


# ── Sync display ───────────────────────────────────────────────────────────────

def _sync_pos_text(pos):
    bar  = (pos // 16) + 1
    beat = ((pos % 16) // 4) + 1
    step = (pos % 4) + 1
    return f"{pos} ({bar}.{beat}.{step})"


def _update_sync_display():
    if not dpg.does_item_exist("midi_sync_state"):
        return
    dpg.set_value("midi_sync_state", _sync_transport_state)
    dpg.configure_item("midi_bpm_value_draw",
                       text=f"{_sync_bpm:.1f}" if _sync_bpm else "--")
    dpg.set_value("midi_sync_clock_count", str(_sync_clock_count))
    dpg.set_value("midi_sync_beats", str(_sync_clock_count // 24))
    dpg.set_value("midi_sync_song_pos", _sync_pos_text(_sync_song_position))
    _update_sync_buttons()


def _update_sync_buttons():
    if not dpg.does_item_exist("midi_sync_start_bg"):
        return
    NEUTRAL_BG   = [55, 55, 55, 255]
    NEUTRAL_ICON = [200, 200, 200, 255]
    GREEN_BG     = [30, 130, 75, 255]
    RED_BG       = [150, 48, 48, 255]
    BRIGHT       = [255, 255, 255, 255]

    for bg, icons in [
        ("midi_sync_start_bg",    ["midi_sync_start_icon"]),
        ("midi_sync_continue_bg", ["midi_sync_continue_bar", "midi_sync_continue_icon"]),
        ("midi_sync_stop_bg",     ["midi_sync_stop_icon"]),
    ]:
        dpg.configure_item(bg, fill=NEUTRAL_BG)
        for icon in icons:
            dpg.configure_item(icon, fill=NEUTRAL_ICON)

    if _sync_transport_state == "Running":
        dpg.configure_item("midi_sync_start_bg",   fill=GREEN_BG)
        dpg.configure_item("midi_sync_start_icon", fill=BRIGHT)
        dpg.configure_item("midi_sync_state_dot",  fill=GREEN_BG)
    elif _sync_transport_state == "Continuing":
        dpg.configure_item("midi_sync_continue_bg",   fill=GREEN_BG)
        dpg.configure_item("midi_sync_continue_bar",  fill=BRIGHT)
        dpg.configure_item("midi_sync_continue_icon", fill=BRIGHT)
        dpg.configure_item("midi_sync_state_dot",     fill=GREEN_BG)
    elif _sync_transport_state == "Stopped":
        dpg.configure_item("midi_sync_stop_bg",   fill=RED_BG)
        dpg.configure_item("midi_sync_stop_icon", fill=BRIGHT)
        dpg.configure_item("midi_sync_state_dot", fill=RED_BG)
    else:
        dpg.configure_item("midi_sync_state_dot", fill=[80, 80, 80, 255])


# ── Sync send ──────────────────────────────────────────────────────────────────

def send_sync_start(*_):
    global _sync_transport_state
    if not _output_ready():
        return
    _driver.send([MIDI_START])
    _sync_transport_state = "Running"
    _update_sync_display()
    _midi_log("Tx", _fmt([MIDI_START]), "transport")


def send_sync_continue(*_):
    global _sync_transport_state
    if not _output_ready():
        return
    _driver.send([MIDI_CONTINUE])
    _sync_transport_state = "Continuing"
    _update_sync_display()
    _midi_log("Tx", _fmt([MIDI_CONTINUE]), "transport")


def send_sync_stop(*_):
    global _sync_transport_state
    if not _output_ready():
        return
    _driver.send([MIDI_STOP])
    stop_midi_notes()
    _sync_transport_state = "Stopped"
    _update_sync_display()
    _midi_log("Tx", _fmt([MIDI_STOP]), "transport")


# ── MIDI message processing ────────────────────────────────────────────────────

def _process_sync(msg):
    global _sync_clock_count, _sync_bpm, _sync_last_clock_time
    global _sync_transport_state, _sync_song_position
    status = msg[0]
    now = time.perf_counter()

    if status == TIMING_CLOCK:
        _sync_clock_count += 1
        if _sync_last_clock_time is not None:
            interval = now - _sync_last_clock_time
            if interval > 0:
                instant = 60.0 / (interval * 24)
                _sync_bpm = instant if not _sync_bpm else (_sync_bpm * 0.85 + instant * 0.15)
        _sync_last_clock_time = now
        _update_sync_display()
        return "clock"
    elif status == MIDI_START:
        _sync_clock_count = 0
        _sync_transport_state = "Running"
    elif status == MIDI_CONTINUE:
        _sync_transport_state = "Continuing"
    elif status == MIDI_STOP:
        _sync_transport_state = "Stopped"
    elif status == SONG_POSITION:
        d1 = msg[1] if len(msg) > 1 else 0
        d2 = msg[2] if len(msg) > 2 else 0
        _sync_song_position = d1 | (d2 << 7)
        _update_sync_display()
        return "songpos"

    _update_sync_display()
    return "transport"


def _process_midi_message(message):
    global _pitch_bend, _mod_wheel
    msg, delta = message
    if not msg:
        return
    status  = msg[0]
    sc      = _status_class(status)
    note    = msg[1] if len(msg) > 1 else 0
    velocity = msg[2] if len(msg) > 2 else 0
    category = "other"

    if status in (TIMING_CLOCK, MIDI_START, MIDI_CONTINUE, MIDI_STOP, SONG_POSITION):
        category = _process_sync(msg)
    elif sc == NOTE_ON and velocity > 0:
        category = "note"
        pc = note % 12
        count = _active_pitches[pc][0] if pc in _active_pitches else 0
        _active_pitches[pc] = (count + 1, velocity)
        _update_piano_keys()
    elif sc == NOTE_OFF or (sc == NOTE_ON and velocity == 0):
        category = "note"
        pc = note % 12
        if pc in _active_pitches:
            count, vel = _active_pitches[pc]
            if count <= 1:
                del _active_pitches[pc]
            else:
                _active_pitches[pc] = (count - 1, vel)
        _update_piano_keys()
    elif sc == CONTROL_CHANGE:
        category = "cc"
        if note == MOD_WHEEL:
            _mod_wheel = velocity
            _update_mod_display(_mod_wheel)
        elif note in (ALL_SOUND_OFF, ALL_NOTES_OFF):
            _active_pitches.clear()
            _update_piano_keys()
        _update_cc_bar(note, velocity)
    elif sc == PITCH_BEND:
        category = "pb"
        lsb = msg[1] if len(msg) > 1 else 0
        msb = msg[2] if len(msg) > 2 else 0
        _pitch_bend = lsb | (msb << 7)
        _update_pitch_display(_pitch_bend)

    if dpg.does_item_exist("midi_raw_hex") and dpg.get_value("midi_raw_hex"):
        text = _fmt_raw(msg, delta)
    else:
        text = _fmt(msg, delta)
    _midi_log("Rx", text, category)


# ── Logging ────────────────────────────────────────────────────────────────────

def _midi_log(direction, text, category="other"):
    if not dpg.does_item_exist("midi_log_window"):
        return
    if direction in ("Rx", "Tx"):
        filters = {
            "note":      "midi_filter_notes",
            "cc":        "midi_filter_cc",
            "pb":        "midi_filter_pb",
            "clock":     "midi_filter_clock",
            "transport": "midi_filter_transport",
            "songpos":   "midi_filter_songpos",
        }
        tag = filters.get(category)
        if tag and dpg.does_item_exist(tag) and not dpg.get_value(tag):
            return
    elif direction == "SYS":
        if dpg.does_item_exist("midi_filter_sys") and not dpg.get_value("midi_filter_sys"):
            return

    entry = f"[SYS] {text}" if direction == "SYS" else f"{direction}{text}"
    dpg.add_text(entry, parent="midi_log_window")
    children = dpg.get_item_children("midi_log_window", 1)
    if len(children) > 30:
        dpg.delete_item(children[0])
    dpg.set_y_scroll("midi_log_window", 9999999)


def _fmt_raw(msg, delta=None):
    hex_bytes = ', '.join(f'{b:02X}' for b in msg)
    ch = _channel(msg[0])
    text = f"[{ch}] | Msg: [{hex_bytes}]"
    if delta is not None:
        text += f" | Dt: {delta:.4f}s"
    return text


def _fmt(msg, delta=None):
    status = msg[0]
    sc = _status_class(status)
    ch = _channel(status)
    d1 = msg[1] if len(msg) > 1 else 0
    d2 = msg[2] if len(msg) > 2 else 0
    ch_str = f"[{ch}]" if ch is not None else "[-]"

    _MSG_NAMES = {
        NOTE_OFF: "Note Off", NOTE_ON: "Note On", CONTROL_CHANGE: "Control",
        PITCH_BEND: "Pitch Bend", PROGRAM_CHANGE: "Program",
        TIMING_CLOCK: "Clock", MIDI_START: "Start",
        MIDI_CONTINUE: "Continue", MIDI_STOP: "Stop",
        SONG_POSITION: "Song Pos",
    }
    name = _MSG_NAMES.get(status, _MSG_NAMES.get(sc, f"0x{status:02X}"))
    text = f"{ch_str} | {name:<10} [{status:02X}]"

    if sc in (NOTE_OFF, NOTE_ON):
        text += f" | Note: {d1:3d} ({_note_name(d1)}) | Vel: {d2:3d}"
    elif sc == CONTROL_CHANGE:
        text += f" | CC: {d1} ({CC_NAMES.get(d1,'')}) | Val: {d2:3d}"
    elif sc == PITCH_BEND:
        text += f" | Bend: {d1 | (d2 << 7):5d}"
    elif status == SONG_POSITION:
        text += f" | Pos: {d1 | (d2 << 7):5d}"
    elif status in (TIMING_CLOCK, MIDI_START, MIDI_CONTINUE, MIDI_STOP):
        text += " | Sync"

    if delta is not None:
        text += f" | Dt: {delta:.4f}s"
    return text


# ── CC monitor ──────────────────────────────────────────────────────────────────

def _update_cc_bar(cc_num, value):
    if dpg.does_item_exist(f"midi_cc_pb_{cc_num}"):
        dpg.configure_item(f"midi_cc_pb_{cc_num}",
                           default_value=value / 127.0, overlay=str(value))
    else:
        if not dpg.does_item_exist("midi_cc_window"):
            return
        name = CC_NAMES.get(cc_num, "")
        grp = dpg.add_group(horizontal=True, parent="midi_cc_window",
                            tag=f"midi_cc_grp_{cc_num}")
        dpg.add_text(f"CC{cc_num:3d} {name:<7}", parent=grp)
        dpg.add_progress_bar(default_value=value / 127.0, width=-1,
                             tag=f"midi_cc_pb_{cc_num}", overlay=str(value), parent=grp)


def reset_cc(*_):
    if not dpg.does_item_exist("midi_cc_window"):
        return
    for child in dpg.get_item_children("midi_cc_window", 1):
        dpg.delete_item(child)


# ── Output note controls ───────────────────────────────────────────────────────

def panic_all(*_):
    if not _output_ready():
        return
    for ch in range(16):
        _driver.stop_all(ch)
    _active_pitches.clear()
    _update_piano_keys()
    _midi_log("SYS", "Panic: all notes off on all 16 channels.")


# ── Program Change ─────────────────────────────────────────────────────────────

def _pc_channel() -> int:
    val = dpg.get_value("midi_out_channel") if dpg.does_item_exist("midi_out_channel") else "0"
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _send_program_change():
    global _pc_bank_msb, _pc_bank_lsb, _pc_program
    if not _output_ready():
        return
    ch = _pc_channel()
    if _pc_mode == "Roland":
        _driver.send_cc(0,  _pc_bank_msb, ch)
        _driver.send_cc(32, 0,            ch)
    elif _pc_mode == "Yamaha":
        _driver.send_cc(0,  _pc_bank_msb, ch)
        _driver.send_cc(32, _pc_bank_lsb, ch)
    _driver.send([PROGRAM_CHANGE | ch, _pc_program])
    _midi_log("Tx", f"PC | mode={_pc_mode} bank={_pc_bank_msb}/{_pc_bank_lsb} prog={_pc_program + 1}", "other")
    if dpg.does_item_exist("midi_pc_program"):
        dpg.set_value("midi_pc_program", _pc_program + 1)


def pc_next(*_):
    global _pc_program, _pc_bank_msb
    if _pc_mode == "GM":
        _pc_program = (_pc_program + 1) % 128
    else:
        _pc_program += 1
        if _pc_program > 127:
            _pc_program = 0
            _pc_bank_msb = min(_pc_bank_msb + 1, 127)
            if dpg.does_item_exist("midi_pc_bank_msb"):
                dpg.set_value("midi_pc_bank_msb", _pc_bank_msb)
    _send_program_change()


def pc_prev(*_):
    global _pc_program, _pc_bank_msb
    if _pc_mode == "GM":
        _pc_program = (_pc_program - 1) % 128
    else:
        _pc_program -= 1
        if _pc_program < 0:
            _pc_program = 127
            _pc_bank_msb = max(_pc_bank_msb - 1, 0)
            if dpg.does_item_exist("midi_pc_bank_msb"):
                dpg.set_value("midi_pc_bank_msb", _pc_bank_msb)
    _send_program_change()


def _on_pc_mode_change(sender, app_data):
    global _pc_mode
    _pc_mode = app_data
    gm = _pc_mode == "GM"
    for tag in ("midi_pc_bank_msb_grp", "midi_pc_bank_lsb_grp"):
        if dpg.does_item_exist(tag):
            dpg.configure_item(tag, show=not gm)
    if dpg.does_item_exist("midi_pc_bank_lsb_grp"):
        dpg.configure_item("midi_pc_bank_lsb_grp", show=_pc_mode == "Yamaha")


def _on_pc_bank_msb_change(sender, app_data):
    global _pc_bank_msb
    _pc_bank_msb = max(0, min(127, int(app_data)))


def _on_pc_bank_lsb_change(sender, app_data):
    global _pc_bank_lsb
    _pc_bank_lsb = max(0, min(127, int(app_data)))


def _on_pc_program_change(sender, app_data):
    global _pc_program
    _pc_program = max(0, min(127, int(app_data) - 1))


# ── Chord output ───────────────────────────────────────────────────────────────

_sounding_midi_notes: list = []   # notes sent in the last send_chord_midi call


def _hex_on() -> bool:
    return dpg.does_item_exist("midi_raw_hex") and dpg.get_value("midi_raw_hex")


def stop_midi_notes():
    """Send note-offs for all currently sounding MIDI notes and clear the list."""
    global _sounding_midi_notes
    if not _driver or _driver._out_port is None:
        return
    ch = 0
    if dpg.does_item_exist("midi_out_channel"):
        val = dpg.get_value("midi_out_channel")
        try:
            ch = int(val)
        except (ValueError, TypeError):
            ch = 0
    for note in _sounding_midi_notes:
        _driver.note_off(note, ch)
        msg = [NOTE_OFF | ch, note, 0]
        _midi_log("Tx", _fmt_raw(msg) if _hex_on() else _fmt(msg), "note")
    _sounding_midi_notes = []


def send_chord_midi(midi_notes: list, velocity: int = 100):
    """Send note-offs for the previous chord and note-ons for the new one.

    Uses the channel selected in the MIDI tab output combo (0 if no UI yet).
    Does nothing if no output port is connected.
    """
    global _sounding_midi_notes
    if not _driver or _driver._out_port is None:
        return

    ch = 0
    if dpg.does_item_exist("midi_out_channel"):
        val = dpg.get_value("midi_out_channel")
        try:
            ch = int(val)
        except (ValueError, TypeError):
            ch = 0

    for note in _sounding_midi_notes:
        _driver.note_off(note, ch)
    _sounding_midi_notes = list(midi_notes)
    hex_mode = _hex_on()
    for note in midi_notes:
        _driver.note_on(note, velocity, ch)
        msg = [NOTE_ON | ch, note, velocity]
        _midi_log("Tx", _fmt_raw(msg) if hex_mode else _fmt(msg), "note")


# ── Event drain (call each frame) ──────────────────────────────────────────────

def drain_ui_events():
    while True:
        try:
            event = _ui_events.get_nowait()
        except queue.Empty:
            break
        kind = event[0]
        if kind == "midi":
            _process_midi_message(event[1])
        elif kind == "ports":
            _process_port_change(event[1], event[2])
        elif kind == "sys":
            _midi_log("SYS", event[1])


# ── UI construction ────────────────────────────────────────────────────────────

_ICON_W, _ICON_H = 44, 46


def _build_sync_section():
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        # Start button
        with dpg.drawlist(width=_ICON_W, height=_ICON_H, tag="midi_sync_start_btn"):
            dpg.draw_rectangle([0,0],[_ICON_W-1,_ICON_H-1],
                               fill=[55,55,55,255], color=[80,80,80,255],
                               rounding=3, tag="midi_sync_start_bg")
            dpg.draw_triangle([13,13],[13,33],[31,23],
                              fill=[200,200,200,255], color=[0,0,0,0],
                              tag="midi_sync_start_icon")
        with dpg.item_handler_registry(tag="midi_sync_start_hreg"):
            dpg.add_item_clicked_handler(callback=send_sync_start)
        dpg.bind_item_handler_registry("midi_sync_start_btn", "midi_sync_start_hreg")

        dpg.add_spacer(width=4)

        # Continue button
        with dpg.drawlist(width=_ICON_W, height=_ICON_H, tag="midi_sync_continue_btn"):
            dpg.draw_rectangle([0,0],[_ICON_W-1,_ICON_H-1],
                               fill=[55,55,55,255], color=[80,80,80,255],
                               rounding=3, tag="midi_sync_continue_bg")
            dpg.draw_rectangle([10,13],[15,33],
                               fill=[200,200,200,255], color=[0,0,0,0],
                               tag="midi_sync_continue_bar")
            dpg.draw_triangle([18,13],[18,33],[32,23],
                              fill=[200,200,200,255], color=[0,0,0,0],
                              tag="midi_sync_continue_icon")
        with dpg.item_handler_registry(tag="midi_sync_continue_hreg"):
            dpg.add_item_clicked_handler(callback=send_sync_continue)
        dpg.bind_item_handler_registry("midi_sync_continue_btn", "midi_sync_continue_hreg")

        dpg.add_spacer(width=4)

        # Stop button
        with dpg.drawlist(width=_ICON_W, height=_ICON_H, tag="midi_sync_stop_btn"):
            dpg.draw_rectangle([0,0],[_ICON_W-1,_ICON_H-1],
                               fill=[55,55,55,255], color=[80,80,80,255],
                               rounding=3, tag="midi_sync_stop_bg")
            dpg.draw_rectangle([11,13],[33,33],
                               fill=[200,200,200,255], color=[0,0,0,0],
                               tag="midi_sync_stop_icon")
        with dpg.item_handler_registry(tag="midi_sync_stop_hreg"):
            dpg.add_item_clicked_handler(callback=send_sync_stop)
        dpg.bind_item_handler_registry("midi_sync_stop_btn", "midi_sync_stop_hreg")

        dpg.add_spacer(width=16)

        with dpg.drawlist(width=190, height=_ICON_H, tag="midi_bpm_canvas"):
            dpg.draw_rectangle([0,0],[189,_ICON_H-1],
                               fill=[18,18,24,255], color=[55,55,72,255], rounding=4)
            dpg.draw_text([12,7], "--", color=[100,210,255,255], size=28,
                          tag="midi_bpm_value_draw")
            dpg.draw_text([152,16], "BPM", color=[85,85,108,255], size=13)

    dpg.add_spacer(height=4)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        with dpg.table(header_row=True, borders_innerV=True,
                    policy=dpg.mvTable_SizingFixedFit, width=-20):
            dpg.add_table_column(label="State",    width_fixed=True, init_width_or_weight=110)
            dpg.add_table_column(label="Clocks",   width_fixed=True, init_width_or_weight=65)
            dpg.add_table_column(label="Beats",    width_fixed=True, init_width_or_weight=50)
            dpg.add_table_column(label="Song Pos", width_fixed=True, init_width_or_weight=130)
            with dpg.table_row():
                with dpg.group(horizontal=True):
                    with dpg.drawlist(width=14, height=14):
                        dpg.draw_circle([7,7], 5, fill=[150,48,48,255],
                                        color=[0,0,0,0], tag="midi_sync_state_dot")
                    dpg.add_spacer(width=4)
                    dpg.add_text("Stopped", tag="midi_sync_state")
                dpg.add_text("0", tag="midi_sync_clock_count")
                dpg.add_text("0", tag="midi_sync_beats")
                dpg.add_text(_sync_pos_text(0), tag="midi_sync_song_pos")


def build_midi_tab():
    """Build the MIDI tab content. Called inside a dpg.tab() context."""
    if not _RTMIDI_OK:
        dpg.add_spacer(height=20)
        dpg.add_text("python-rtmidi is not installed.", color=[255, 100, 100, 255])
        dpg.add_text("Run: pip install python-rtmidi", color=[180, 180, 180, 255])
        return

    # ── Ports ─────────────────────────────────────────────────────────────────────
    
    if not dpg.does_item_exist("__midi_panic_theme__"):
        with dpg.theme(tag="__midi_panic_theme__"):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button,        [180, 40, 40, 255])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [220, 50, 50, 255])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive,  [140, 30, 30, 255])
                dpg.add_theme_color(dpg.mvThemeCol_Text,          [255, 255, 255, 255])
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)

    dpg.add_spacer(height=2)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        dpg.add_text("Ports", color=COLOR_ACCENT)
        dpg.add_spacer(width=150)
        dpg.add_checkbox(label="Auto-Connect Single Device",
                        tag="midi_auto_connect", default_value=False)
        dpg.add_spacer(width=20)
        dpg.add_button(label="Panic All Channels", callback=panic_all, width=170, tag="midi_panic_btn")
        dpg.bind_item_theme("midi_panic_btn", "__midi_panic_theme__")
    dpg.add_separator()

    with dpg.table(header_row=False, borders_innerV=True,
                   policy=dpg.mvTable_SizingStretchSame):
        dpg.add_table_column()
        dpg.add_table_column()
        with dpg.table_row():
            with dpg.group():
                dpg.add_spacer(height=4)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=20)
                    dpg.add_text("Input", color=COLOR_TEXT_DIM)
                    dpg.add_combo(["None"] + _ins, tag="midi_in_port",
                                  default_value="None", width=200)
                    dpg.add_spacer(width=12)
                    dpg.add_text("Channel", color=COLOR_TEXT_DIM)
                    dpg.add_combo(_CHANNEL_OPTIONS, tag="midi_in_channel",
                                  default_value="All", width=-20)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=20)
                    dpg.add_button(label="Connect Input", callback=connect_input, width=-20)
                dpg.add_spacer(height=4)
            with dpg.group():
                dpg.add_spacer(height=4)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=20)
                    dpg.add_text("Output", color=COLOR_TEXT_DIM)
                    dpg.add_combo(["None"] + _outs, tag="midi_out_port",
                                  default_value="None", width=200)
                    dpg.add_spacer(width=12)
                    dpg.add_text("Channel", color=COLOR_TEXT_DIM)
                    dpg.add_combo(_CHANNEL_OPTIONS, tag="midi_out_channel",
                                  default_value="All", width=-20)
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=20)
                    dpg.add_button(label="Connect Output", callback=connect_output, width=-20)
                dpg.add_spacer(height=4)
    dpg.add_separator()

    # ── Program Change ────────────────────────────────────────────────────────────
    dpg.add_spacer(height=4)
    dpg.add_text("Program Change", color=COLOR_ACCENT)
    dpg.add_separator()
    dpg.add_spacer(height=4)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        dpg.add_combo(_PC_MODES, default_value="GM", tag="midi_pc_mode",
                      width=90, callback=_on_pc_mode_change)
        
        with dpg.group(horizontal=True, tag="midi_pc_bank_lsb_grp", show=False):
            dpg.add_spacer(width=12)
            dpg.add_text("LSB")
            dpg.add_spacer(width=4)
            dpg.add_input_int(default_value=0, tag="midi_pc_bank_lsb",
                              min_value=0, max_value=127, width=80,
                              callback=_on_pc_bank_lsb_change)
        dpg.add_spacer(width=30)
        dpg.add_button(label="\u25c0 Prev", callback=pc_prev, width=65)
        dpg.add_spacer(width=4)
        dpg.add_button(label="Next \u25b6", callback=pc_next, width=65)
        dpg.add_spacer(width=30)
        with dpg.group(horizontal=True, tag="midi_pc_bank_msb_grp", show=False):
            dpg.add_spacer(width=12)
            dpg.add_text("Bank", color=COLOR_TEXT_DIM)
            dpg.add_input_int(default_value=0, tag="midi_pc_bank_msb",
                              min_value=0, max_value=127, width=80,
                              callback=_on_pc_bank_msb_change)
        dpg.add_text("Prog", color=COLOR_TEXT_DIM)
        dpg.add_input_int(default_value=1, tag="midi_pc_program",
                    min_value=1, max_value=128, width=100,
                    callback=_on_pc_program_change)
        dpg.add_spacer(width=20)
        dpg.add_button(label="Send", callback=_send_program_change, width=-20)
    dpg.add_spacer(height=3)
    dpg.add_separator()
    dpg.add_spacer(height=4)

    # ── Sync | MIDI Input ─────────────────────────────────────────────────────────
    with dpg.table(header_row=False, borders_innerV=True,
                   policy=dpg.mvTable_SizingStretchSame):
        dpg.add_table_column()
        dpg.add_table_column()
        with dpg.table_row():
            with dpg.group():
                dpg.add_text("MIDI Input", color=COLOR_ACCENT)
                dpg.add_separator()
                dpg.add_spacer(height=12)
                
                with dpg.group(horizontal=True):
                    dpg.add_spacer(width=40)
                    with dpg.group():
                        with dpg.drawlist(width=22, height=64, tag="midi_pitch_canvas"):
                            dpg.draw_rectangle([0,0],[21,63],
                                               fill=[25,25,25,255], color=[90,90,90,255])
                            dpg.draw_line([0,_PB_CENTER],[21,_PB_CENTER],
                                          color=[70,70,70,255])
                            dpg.draw_rectangle([1,_PB_CENTER],[20,_PB_CENTER+1],
                                               fill=[100,180,255,255], color=[0,0,0,0],
                                               tag="midi_pitch_fill")
                        dpg.add_text("BEND", color=COLOR_TEXT_DIM)
                    dpg.add_spacer(width=6)
                    with dpg.group():
                        with dpg.drawlist(width=22, height=64, tag="midi_mod_canvas"):
                            dpg.draw_rectangle([0,0],[21,63],
                                               fill=[25,25,25,255], color=[90,90,90,255])
                            dpg.draw_rectangle([1,63],[20,63],
                                               fill=[100,255,150,255], color=[0,0,0,0],
                                               tag="midi_mod_fill")
                        dpg.add_text("MOD", color=COLOR_TEXT_DIM)
                    dpg.add_spacer(width=12)
                    with dpg.drawlist(width=7*_WW, height=_WH, tag="midi_piano_canvas"):
                        for i, pc in enumerate(_WHITE_PC):
                            x = i * _WW
                            dpg.draw_rectangle([x,0],[x+_WW-1,_WH-1],
                                               fill=[255,255,255,255], color=[80,80,80,255],
                                               tag=f"midi_wkey_{pc}")
                        for pc, bx in zip(_BLACK_PC, _BLACK_X):
                            dpg.draw_rectangle([bx,0],[bx+_BW-1,_BH-1],
                                               fill=[20,20,20,255], color=[0,0,0,255],
                                               tag=f"midi_bkey_{pc}")
            with dpg.group():
                dpg.add_text("Sync", color=COLOR_ACCENT)
                dpg.add_separator()
                dpg.add_spacer(height=6)
                _build_sync_section()

    # ── CC Monitor ────────────────────────────────────────────────────────────────
    dpg.add_spacer(height=4)
    dpg.add_text("CC Monitor", color=COLOR_ACCENT)
    dpg.add_separator()
    dpg.add_spacer(height=4)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        dpg.add_button(label="Clear", callback=reset_cc, width=60)
    dpg.add_spacer(height=4)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        with dpg.child_window(tag="midi_cc_window", width=-20, height=220):
            pass

    # ── Log ───────────────────────────────────────────────────────────────────────
    dpg.add_spacer(height=8)
    dpg.add_text("Log", color=COLOR_ACCENT)
    dpg.add_separator()
    dpg.add_spacer(height=4)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        with dpg.group(horizontal=True):
            dpg.add_checkbox(label="Notes",     tag="midi_filter_notes",     default_value=True)
            dpg.add_spacer(width=4)
            dpg.add_checkbox(label="CC",        tag="midi_filter_cc",        default_value=True)
            dpg.add_spacer(width=4)
            dpg.add_checkbox(label="PB",        tag="midi_filter_pb",        default_value=True)
            dpg.add_spacer(width=4)
            dpg.add_checkbox(label="Clock",     tag="midi_filter_clock",     default_value=False)
            dpg.add_spacer(width=4)
            dpg.add_checkbox(label="Tpt",       tag="midi_filter_transport", default_value=True)
            dpg.add_spacer(width=4)
            dpg.add_checkbox(label="Pos",       tag="midi_filter_songpos",   default_value=True)
            dpg.add_spacer(width=4)
            dpg.add_checkbox(label="SYS",       tag="midi_filter_sys",       default_value=True)
        dpg.add_spacer(width=-1)
        dpg.add_checkbox(label="Hex Display",   tag="midi_raw_hex",      default_value=False)
    dpg.add_spacer(height=4)
    with dpg.group(horizontal=True):
        dpg.add_spacer(width=20)
        with dpg.child_window(tag="midi_log_window", width=-20, height=-20):
            pass

    _auto_connect()

"""
Piano keyboard rendering on a Dear PyGui drawlist.

Shows one octave (C to B) with highlighted keys, plus multi-octave
pianos for chord progression details.
Chord notes highlight in gold, scale notes in blue.
The bass note (lowest sounding note) highlights in green.
"""

from __future__ import annotations

import dearpygui.dearpygui as dpg
from typing import List, Set

# ── Piano key geometry ─────────────────────────────────────────────────────────
_PWW, _PWH = 48, 120   # white key width / height
_PBW, _PBH = 30, 72    # black key width / height
_WHITE_PC = [0, 2, 4, 5, 7, 9, 11]
_BLACK_PC = [1, 3, 6, 8, 10]
_BLACK_X  = [
    _PWW - _PBW // 2,
    2 * _PWW - _PBW // 2,
    4 * _PWW - _PBW // 2,
    5 * _PWW - _PBW // 2,
    6 * _PWW - _PBW // 2,
]
PIANO_CANVAS_W = 7 * _PWW + 2
PIANO_CANVAS_H = _PWH + 4

# Multi-octave piano used in the progression tab
PROG_PIANO_OCTAVES = 2
PROG_PIANO_CANVAS_W = PROG_PIANO_OCTAVES * 7 * _PWW + 2
PROG_PIANO_CANVAS_H = _PWH + 4


# ── Single-octave piano ────────────────────────────────────────────────────────

def build_piano_keys(canvas_tag: str):
    """Draw the static piano key shapes once."""
    for i, pc in enumerate(_WHITE_PC):
        x = i * _PWW
        dpg.draw_rectangle(
            [x, 0], [x + _PWW - 2, _PWH],
            fill=[255, 255, 255, 255], color=[60, 60, 70, 255],
            tag="piano_wkey_" + str(pc), parent=canvas_tag,
        )
    for i, pc in enumerate(_BLACK_PC):
        x = _BLACK_X[i]
        dpg.draw_rectangle(
            [x, 0], [x + _PBW, _PBH],
            fill=[20, 20, 20, 255], color=[0, 0, 0, 0],
            tag="piano_bkey_" + str(pc), parent=canvas_tag,
        )


def update_piano_keys(chord_pcs: Set[int], scale_pcs: Set[int],
                      bass_pc: int = -1):
    """Highlight keys based on chord, scale, and bass note.

    chord_pcs: pitch classes in the chord (gold = chord, blue = scale only)
    bass_pc:   pitch class of the lowest sounding note (green)
    """
    for pc in _WHITE_PC:
        tag = "piano_wkey_" + str(pc)
        if not dpg.does_item_exist(tag):
            continue
        if pc == bass_pc and pc in chord_pcs:
            fill = [80, 230, 80, 255]    # green for bass
        elif pc in chord_pcs:
            fill = [255, 210, 50, 255]   # gold for chord
        elif pc in scale_pcs:
            fill = [100, 180, 255, 255]  # blue for scale only
        else:
            fill = [255, 255, 255, 255]  # white
        dpg.configure_item(tag, fill=fill)

    for pc in _BLACK_PC:
        tag = "piano_bkey_" + str(pc)
        if not dpg.does_item_exist(tag):
            continue
        if pc == bass_pc and pc in chord_pcs:
            fill = [40, 180, 40, 255]     # dark green for bass
        elif pc in chord_pcs:
            fill = [200, 160, 30, 255]   # gold for chord
        elif pc in scale_pcs:
            fill = [40, 80, 180, 255]    # blue for scale only
        else:
            fill = [20, 20, 20, 255]     # black
        dpg.configure_item(tag, fill=fill)


# ── Multi-octave piano (for chord progression detail) ──────────────────────────

def _octave_offset(octave: int) -> int:
    """Return the x-offset for a given octave."""
    return octave * 7 * _PWW


def build_multi_octave_piano(canvas_tag: str, start_octave: int = 3):
    """Draw a multi-octave piano centered around *start_octave*.
    
    Draws PROG_PIANO_OCTAVES octaves with the lowest being start_octave-1.
    For example start_octave=3 draws C2-B4 (octaves 2,3,4).
    Tags use MIDI note numbers so update functions can highlight them.
    """
    base_midi = (start_octave - 1) * 12  # MIDI of C in the lowest octave shown
    for oct in range(PROG_PIANO_OCTAVES):
        ox = _octave_offset(oct)
        for i, pc in enumerate(_WHITE_PC):
            x = ox + i * _PWW
            midi = base_midi + oct * 12 + pc
            dpg.draw_rectangle(
                [x, 0], [x + _PWW - 2, _PWH],
                fill=[255, 255, 255, 255], color=[60, 60, 70, 255],
                tag=f"mpiano_wkey_{midi}", parent=canvas_tag,
            )
        for i, pc in enumerate(_BLACK_PC):
            x = ox + _BLACK_X[i]
            midi = base_midi + oct * 12 + pc
            dpg.draw_rectangle(
                [x, 0], [x + _PBW, _PBH],
                fill=[20, 20, 20, 255], color=[0, 0, 0, 0],
                tag=f"mpiano_bkey_{midi}", parent=canvas_tag,
            )



def _prog_piano_midi_range(start_octave: int = 3):
    """Return (start_midi, end_midi) for the multi-octave piano."""
    base = (start_octave - 1) * 12
    return base, base + PROG_PIANO_OCTAVES * 12


def update_multi_octave_piano(canvas_tag: str, midi_notes: List[int],
                               bass_midi: int = -1,
                               start_octave: int = 3):
    """Highlight multi-octave piano keys by MIDI note numbers."""
    note_set = set(midi_notes)
    lo, hi = _prog_piano_midi_range(start_octave)
    for midi in range(lo, hi):
        pc = midi % 12
        is_white = pc in _WHITE_PC
        prefix = "mpiano_wkey_" if is_white else "mpiano_bkey_"
        tag = prefix + str(midi)
        if not dpg.does_item_exist(tag):
            continue
        if midi == bass_midi and midi in note_set:
            fill = [80, 230, 80, 255] if is_white else [40, 180, 40, 255]
        elif midi in note_set:
            fill = [255, 210, 50, 255] if is_white else [200, 160, 30, 255]
        else:
            fill = [255, 255, 255, 255] if is_white else [20, 20, 20, 255]
        dpg.configure_item(tag, fill=fill)


def clear_multi_octave_piano(canvas_tag: str, start_octave: int = 3):
    """Reset all multi-octave piano keys to their default colors."""
    lo, hi = _prog_piano_midi_range(start_octave)
    for midi in range(lo, hi):
        pc = midi % 12
        is_white = pc in _WHITE_PC
        prefix = "mpiano_wkey_" if is_white else "mpiano_bkey_"
        tag = prefix + str(midi)
        if not dpg.does_item_exist(tag):
            continue
        fill = [255, 255, 255, 255] if is_white else [20, 20, 20, 255]
        dpg.configure_item(tag, fill=fill)


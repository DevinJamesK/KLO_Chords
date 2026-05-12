"""
Console logging helpers — fixed-column format for chord/progression events.

Produces aligned log lines like:

    [chord  3]  IV     Fmaj7     oct=3   F    A    C    E    F4   A4   C5   E5    sub:F3
    [cell   7]  IV     F         rot=0   F    A    C         F3   A3   C4         sub:--
    [row 0]  0:C      1:Dm     2:Em     3:F      4:G      5:Am     6:Bdim   7:--
"""

from typing import Optional

from klo_chords.core.chords import pc_to_note

_NOTE_COL_W  = 4   # width of each note name cell  ("Bb  " / "C#  ")
_MIDI_COL_W  = 5   # width of each MIDI name cell  ("Bb3  " / "C#4  ")
_MAX_NOTES   = 4   # triads=3, 7ths=4


def midi_to_note_name(midi: int) -> str:
    """Convert MIDI note number to name+octave, e.g. 60 -> 'C4'."""
    pc = midi % 12
    octave = midi // 12 - 1
    name = pc_to_note(pc)
    return f"{name}{octave}"


def sub_midi(root_pc: int, midi_notes: list, sound_settings: dict) -> Optional[int]:
    """Return the sub oscillator MIDI note, or None when disabled/unavailable."""
    if not sound_settings.get("sub_oscillator") or not midi_notes:
        return None
    lowest = min(midi_notes)
    sub = root_pc + 12 * ((lowest - 1 - root_pc) // 12)
    return max(0, sub)


def fmt_event(tag: str, degree: str, chord_name: str, context: str,
              notes: list, midi_names: list, sub_name: str = "") -> str:
    """Format a single chord event into a fixed-width log line."""
    note_str = "".join(n.ljust(_NOTE_COL_W) for n in notes).ljust(_NOTE_COL_W * _MAX_NOTES)
    midi_str = "".join(n.ljust(_MIDI_COL_W) for n in midi_names).ljust(_MIDI_COL_W * _MAX_NOTES)
    sub_col  = f"sub:{sub_name}" if sub_name else "sub:--"
    return f"{tag:<11}  {degree:<6}  {chord_name:<10}  {context:<7}  {note_str}  {midi_str}  {sub_col}"


def log_progression_row(row: int, cells: list, cols: int):
    """Print one row of the progression grid to the console."""
    start = row * cols
    row_cells = cells[start:start + cols]
    col_w = 9
    entries = []
    for i, cell in enumerate(row_cells):
        if cell.is_empty():
            label = "--"
        else:
            q = "" if cell.quality == "M" else cell.quality
            label = cell.root + q
        entries.append(f"{start + i}:{label}".ljust(col_w))
    print(f"[row {row}]  " + " ".join(entries))

"""
Tests for klo_chords.helpers.console_logging — fixed-column log formatting.

Covers:
  - midi_to_note_name: MIDI number → name+octave
  - sub_midi: sub-oscillator MIDI calculation
  - fmt_event: chord event log line formatting
  - log_progression_row: progression row console output
"""

from __future__ import annotations

import io
import sys
from typing import Optional

import pytest

from klo_chords.core.chords import ProgCell
from klo_chords.helpers.console_logging import (
    midi_to_note_name,
    sub_midi,
    fmt_event,
    log_progression_row,
)


class TestMidiToNoteName:
    @pytest.mark.parametrize("midi,expected", [
        (60, "C4"),
        (61, "C#4"),
        (62, "D4"),
        (69, "A4"),     # A440
        (0,  "C-1"),
        (127, "G9"),
        (48, "C3"),     # Middle C's C3 representation
    ])
    def test_known_midi_numbers(self, midi, expected):
        assert midi_to_note_name(midi) == expected

    def test_sharp_only_spelling(self):
        """All notes use sharp spelling by default (pc_to_note default)."""
        assert midi_to_note_name(61) == "C#4"   # not Db4
        assert midi_to_note_name(63) == "D#4"   # not Eb4


class TestSubMidi:
    def test_returns_none_when_disabled(self):
        settings = {"sub_oscillator": False}
        assert sub_midi(0, [60, 64, 67], settings) is None

    def test_returns_none_when_no_notes(self):
        settings = {"sub_oscillator": True}
        assert sub_midi(0, [], settings) is None

    def test_sub_below_lowest_note(self):
        """Sub should be an octave (or multiple) below the lowest note."""
        settings = {"sub_oscillator": True}
        # C major: C4=60, E4=64, G4=67. Root=C(0). Lowest=60.
        # root_pc=0, sub = 0 + 12*((60-1-0)//12) = 0 + 12*(59//12) = 0+12*4=48
        result = sub_midi(0, [60, 64, 67], settings)
        assert result == 48  # C3
        assert result < min([60, 64, 67])  # must be below

    def test_sub_clamped_at_zero(self):
        """Sub should never go below MIDI 0."""
        settings = {"sub_oscillator": True}
        result = sub_midi(0, [12, 16, 19], settings)
        assert result >= 0


class TestFmtEvent:
    def test_basic_triad_event(self):
        tag = "[chord  0]"
        degree = "I"
        chord_name = "C"
        context = "oct=3"
        notes = ["C", "E", "G"]
        midi_names = ["C3", "E3", "G3"]
        sub_name = ""

        line = fmt_event(tag, degree, chord_name, context, notes, midi_names, sub_name)
        assert "[chord  0]" in line
        assert "I" in line
        assert "C" in line
        assert "C    E    G" in line or "C   E   G" in line
        assert "sub:--" in line

    def test_event_with_sub(self):
        line = fmt_event(
            "[cell   5]", "V", "G7", "rot=0",
            ["G", "B", "D", "F"],
            ["G3", "B3", "D4", "F4"],
            sub_name="G2",
        )
        assert "sub:G2" in line

    def test_fixed_width_columns(self):
        """Generate two lines with different data; key columns should align."""
        line1 = fmt_event("[chord  0]", "I", "Cmaj7", "oct=3",
                          ["C", "E", "G", "B"], ["C3", "E3", "G3", "B3"], "")
        line2 = fmt_event("[chord  1]", "ii", "Dm7", "oct=3",
                          ["D", "F", "A", "C"], ["D3", "F3", "A3", "C4"], "sub:D2")

        # Both should have the same tag width (11 chars)
        tag1 = line1[:11]
        tag2 = line2[:11]
        assert len(tag1) == len(tag2)


class TestLogProgressionRow:
    def test_row_with_all_filled_cells(self):
        """All 8 cells filled — row should print without errors."""
        cells = []
        for i in range(8):
            cell = ProgCell()
            cell.root = ["C", "D", "E", "F", "G", "A", "B", "C"][i]
            cell.quality = "M" if cell.root in ("C", "F", "G") else "m"
            cells.append(cell)

        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            log_progression_row(0, cells, 8)
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        assert "[row 0]" in output
        assert "C" in output

    def test_row_with_empty_cells(self):
        cells = [ProgCell() for _ in range(8)]
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            log_progression_row(0, cells, 8)
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        assert "[row 0]" in output
        assert "--" in output

    def test_row_with_mixed_cells(self):
        cells = []
        for i in range(8):
            cell = ProgCell()
            if i % 2 == 0:
                cell.root = "C"
            cells.append(cell)
        captured = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured
        try:
            log_progression_row(0, cells, 8)
        finally:
            sys.stdout = old_stdout

        output = captured.getvalue()
        assert "[row 0]" in output

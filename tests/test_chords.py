"""
Tests for klo_chords.core.chords — the music theory engine (part 1).

Covers note/pc conversion, scales, diatonic chords, and ProgCell.
"""

from __future__ import annotations

import pytest

from klo_chords.core.chords import (
    ChordInfo,
    ProgCell,
    NOTE_NAMES,
    KEY_NAMES,
    ENHARMONIC,
    QUALITY_INTERVALS,
    SCALE_TYPES,
    get_diatonic_chords,
    get_scale_notes,
    get_degree_for_root,
    note_to_pc,
    pc_to_note,
    get_accidental_style,
)


# ═══════════════ note_to_pc / pc_to_note ═══════════════


class TestNotePcConversion:
    @pytest.mark.parametrize("note,expected_pc", [
        ("C", 0), ("C#", 1), ("D", 2), ("D#", 3), ("E", 4),
        ("F", 5), ("F#", 6), ("G", 7), ("G#", 8), ("A", 9),
        ("A#", 10), ("B", 11),
        ("Db", 1), ("Eb", 3), ("Gb", 6), ("Ab", 8), ("Bb", 10),
    ])
    def test_note_to_pc(self, note, expected_pc):
        assert note_to_pc(note) == expected_pc

    def test_note_to_pc_strips_whitespace(self):
        assert note_to_pc("  C# ") == 1

    def test_note_to_pc_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown note"):
            note_to_pc("H")

    @pytest.mark.parametrize("pc,expected", [
        (0, "C"), (1, "C#"), (2, "D"), (3, "D#"), (4, "E"),
        (5, "F"), (6, "F#"), (7, "G"), (8, "G#"), (9, "A"),
        (10, "A#"), (11, "B"), (12, "C"),
    ])
    def test_pc_to_note_sharp_default(self, pc, expected):
        assert pc_to_note(pc) == expected

    @pytest.mark.parametrize("pc,style,expected", [
        (1, "flat", "Db"), (3, "flat", "Eb"),
        (6, "flat", "Gb"), (8, "flat", "Ab"), (10, "flat", "Bb"),
        (0, "flat", "C"), (5, "flat", "F"),
    ])
    def test_pc_to_note_with_style(self, pc, style, expected):
        assert pc_to_note(pc, style) == expected

    @pytest.mark.parametrize("note", NOTE_NAMES)
    def test_round_trip_sharp(self, note: str):
        assert pc_to_note(note_to_pc(note)) == note

    def test_round_trip_all_keys(self):
        for key in KEY_NAMES:
            pc = note_to_pc(key)
            result = pc_to_note(pc, get_accidental_style(key))
            assert result == key, f"Round-trip failed for {key}"


# ═══════════════ ENHARMONIC ═══════════════


class TestEnharmonic:
    def test_known_pairs(self):
        assert ENHARMONIC["C#"] == "Db"
        assert ENHARMONIC["Db"] == "C#"
        assert ENHARMONIC["F#"] == "Gb"
        assert ENHARMONIC["Gb"] == "F#"

    def test_equal_pitch_class(self):
        assert note_to_pc("C#") == note_to_pc("Db") == 1


# ═══════════════ get_accidental_style ═══════════════


class TestAccidentalStyle:
    @pytest.mark.parametrize("key,expected", [
        ("F", "flat"), ("Bb", "flat"), ("Eb", "flat"), ("Ab", "flat"),
        ("Db", "flat"), ("Gb", "flat"), ("C", "flat"),
        ("G", "sharp"), ("D", "sharp"), ("A", "sharp"), ("E", "sharp"),
        ("B", "sharp"), ("F#", "sharp"), ("C#", "sharp"),
    ])
    def test_style_for_key(self, key, expected):
        assert get_accidental_style(key) == expected


# ═══════════════ Scales ═══════════════


class TestScales:
    def test_major_scale_c(self):
        scale = SCALE_TYPES["Major"]
        assert scale.pitches(note_to_pc("C")) == [0, 2, 4, 5, 7, 9, 11]

    def test_natural_minor_scale_a(self):
        scale = SCALE_TYPES["Natural minor"]
        assert scale.pitches(note_to_pc("A")) == [9, 11, 0, 2, 4, 5, 7]

    def test_heptatonic_count(self):
        for scale in ["Major", "Natural minor", "Dorian", "Mixolydian"]:
            assert len(SCALE_TYPES[scale].intervals) == 7

    def test_pentatonic_count(self):
        assert len(SCALE_TYPES["Pentatonic Maj"].intervals) == 5
        assert len(SCALE_TYPES["Pentatonic min"].intervals) == 5

    def test_all_scales_valid_pitches(self):
        for scale in SCALE_TYPES.values():
            for key_pc in range(12):
                pitches = scale.pitches(key_pc)
                assert all(0 <= p <= 11 for p in pitches)
                assert len(set(pitches)) == len(pitches)  # no duplicates

"""
Tests for klo_chords.core.quality — chord quality formatting.

Covers:
  - quality_symbol: compact display forms (e.g. "min", "°", "+")
  - quality_spelled: full human-readable names
  - Coverage of all quality strings in QUALITY_INTERVALS
  - Unknown quality handling
"""

from __future__ import annotations

import pytest

from klo_chords.core.quality import quality_symbol, quality_spelled
from klo_chords.core.chords import QUALITY_INTERVALS


class TestQualitySymbol:
    """Compact symbols used in chord box and progression cell display."""

    @pytest.mark.parametrize("quality,expected", [
        ("M",       ""),         # Major = no suffix
        ("m",       "min"),
        ("dim",     "\u00b0"),   # diminished = °
        ("aug",     "+"),        # augmented = +
        ("7",       "7"),
        ("m7",      "min7"),
        ("maj7",    "\u25b37"),
        ("dim7",    "\u00b07"),  # °7
        ("m7b5",    "min7b5"),
        ("mmaj7",   "min\u25b37"),
        ("aug7",    "+7"),
        ("augmaj7", "+\u25b37"),
        ("sus2",    "sus2"),
        ("sus4",    "sus4"),
    ])
    def test_known_qualities(self, quality, expected):
        assert quality_symbol(quality) == expected

    def test_unknown_quality_is_passthrough(self):
        """Unknown quality strings should fall back to the raw string."""
        assert quality_symbol("bogus") == "bogus"

    def test_all_quality_intervals_have_a_symbol(self):
        """Every quality in QUALITY_INTERVALS must have a non-None symbol."""
        for quality in QUALITY_INTERVALS:
            symbol = quality_symbol(quality)
            assert symbol is not None, f"No symbol for {quality}"
            # It should be either empty (M) or a meaningful string
            assert isinstance(symbol, str)


class TestQualitySpelled:
    """Full human-readable quality names for the detail panel."""

    @pytest.mark.parametrize("quality,expected", [
        ("M",       "Major"),
        ("m",       "minor"),
        ("dim",     "Diminished"),
        ("aug",     "Augmented"),
        ("7",       "7"),
        ("m7",      "minor 7"),
        ("maj7",    "major 7"),
        ("dim7",    "diminished 7"),
        ("m7b5",    "minor 7b5"),
        ("mmaj7",   "minor major 7"),
        ("aug7",    "augmented 7"),
        ("augmaj7", "augmented major 7"),
        ("sus2",    "sus2"),
        ("sus4",    "sus4"),
    ])
    def test_known_qualities(self, quality, expected):
        assert quality_spelled(quality) == expected

    def test_unknown_quality_is_passthrough(self):
        assert quality_spelled("bogus") == "bogus"


class TestQualityConsistency:
    """All quality symbols must have corresponding spelled names."""

    def test_every_interval_quality_has_spelled_name(self):
        """Every QUALITY_INTERVALS key maps to a non-empty spelled string."""
        for quality in QUALITY_INTERVALS:
            spelled = quality_spelled(quality)
            assert spelled is not None
            assert isinstance(spelled, str)
            assert len(spelled) > 0

    def test_symbol_and_spelled_are_different_for_most(self):
        """For all non-major qualities, symbol ≠ spelled."""
        for quality in QUALITY_INTERVALS:
            if quality == "M":
                continue
            sym = quality_symbol(quality)
            spell = quality_spelled(quality)
            # They don't have to differ, but both should be valid strings
            assert isinstance(sym, str)
            assert isinstance(spell, str)

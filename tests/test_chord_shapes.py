"""
Automated audit of guitar chord voicings.

Tests fall into two categories:
  1. Curated shape audit  — every hand-entered shape in guitar_standard.json
     must contain only chord tones and must include the root.
  2. Diatonic coverage    — for every key × heptatonic scale × 7th-chord option
     at least one valid voicing must exist for each diatonic chord.
"""

import unittest

from klo_chords.chord_shapes import (
    _load_curated_shapes,
    get_ranked_voicings,
    shape_pitch_classes,
)
from klo_chords.chords import (
    QUALITY_INTERVALS,
    SCALE_TYPES,
    NOTE_NAMES,
    get_diatonic_chords,
    note_to_pc,
    get_all_voicings,
)


HEPTATONIC_SCALES = [
    name for name, scale in SCALE_TYPES.items() if len(scale.intervals) == 7
]


class CuratedShapeAuditTests(unittest.TestCase):
    """Every entry in guitar_standard.json must use only chord tones."""

    def test_no_non_chord_tones_in_curated_shapes(self):
        curated = _load_curated_shapes()
        failures = []
        for (root, quality), shapes in curated.items():
            intervals = QUALITY_INTERVALS.get(quality)
            if intervals is None:
                failures.append(f"unknown quality '{quality}' for {root}")
                continue
            root_pc = note_to_pc(root)
            required = {(root_pc + i) % 12 for i in intervals}
            for shape in shapes:
                played = shape_pitch_classes(shape.frets)
                extra = played - required
                if extra:
                    failures.append(
                        f"{root} {quality} '{shape.fret_string}': "
                        f"extra pitch-classes {extra}"
                    )
        self.assertEqual([], failures, "\n" + "\n".join(failures))

    def test_root_present_in_all_curated_shapes(self):
        curated = _load_curated_shapes()
        failures = []
        for (root, quality), shapes in curated.items():
            root_pc = note_to_pc(root)
            for shape in shapes:
                played = shape_pitch_classes(shape.frets)
                if root_pc not in played:
                    failures.append(
                        f"{root} {quality} '{shape.fret_string}': root {root} missing"
                    )
        self.assertEqual([], failures, "\n" + "\n".join(failures))


class DiatonicVoicingCoverageTests(unittest.TestCase):
    """Every diatonic chord (triads and 7ths) must have at least one valid voicing."""

    def _assert_has_voicing(self, chord, context):
        root_pc = note_to_pc(chord.root)
        required = {(root_pc + i) % 12 for i in chord.intervals}
        voicings = get_ranked_voicings(chord.root, chord.quality, chord.intervals)
        self.assertTrue(
            voicings,
            f"{context}: {chord.root}{chord.quality} has no valid voicing"
        )
        # Double-check first result is actually clean
        played = shape_pitch_classes(voicings[0].frets)
        self.assertFalse(
            played - required,
            f"{context}: {chord.root}{chord.quality} best voicing "
            f"'{voicings[0].fret_string}' has non-chord tones {played - required}"
        )
        self.assertIn(
            root_pc,
            played,
            f"{context}: {chord.root}{chord.quality} best voicing missing root"
        )

    def test_triads_all_keys_all_heptatonic_scales(self):
        for key in NOTE_NAMES:
            for scale_name in HEPTATONIC_SCALES:
                chords = get_diatonic_chords(key, scale_name, include_sevenths=False)
                for chord in chords:
                    with self.subTest(key=key, scale=scale_name, chord=f"{chord.root}{chord.quality}"):
                        self._assert_has_voicing(
                            chord, f"{key} {scale_name} triads"
                        )

    def test_seventh_chords_all_keys_all_heptatonic_scales(self):
        for key in NOTE_NAMES:
            for scale_name in HEPTATONIC_SCALES:
                chords = get_diatonic_chords(key, scale_name, include_sevenths=True)
                for chord in chords:
                    with self.subTest(key=key, scale=scale_name, chord=f"{chord.root}{chord.quality}"):
                        self._assert_has_voicing(
                            chord, f"{key} {scale_name} 7ths"
                        )

    def test_no_unknown_quality_symbols(self):
        """No diatonic chord should produce a '?' quality."""
        bad = []
        for key in NOTE_NAMES:
            for scale_name in HEPTATONIC_SCALES:
                for include_7ths in (False, True):
                    chords = get_diatonic_chords(key, scale_name, include_sevenths=include_7ths)
                    for chord in chords:
                        if "?" in chord.quality:
                            bad.append(
                                f"{key} {scale_name} {'7ths' if include_7ths else 'triads'}: "
                                f"{chord.root}{chord.quality}"
                            )
        self.assertEqual([], bad, "\n" + "\n".join(bad))


class CanonicalShapeRankingTests(unittest.TestCase):
    """Hand-curated open shapes must rank first for their chord."""

    EXPECTED_FIRST_VOICINGS = {
        ("C", "M"):  [(1, 3), (2, 2), (3, 0), (4, 1), (5, 0)],
        ("D", "M"):  [(2, 0), (3, 2), (4, 3), (5, 2)],
        ("E", "m"):  [(0, 0), (1, 2), (2, 2), (3, 0), (4, 0), (5, 0)],
        ("G", "7"):  [(0, 3), (1, 2), (2, 0), (3, 0), (4, 0), (5, 1)],
    }

    INTERVALS_BY_QUALITY = {
        "M":   [0, 4, 7],
        "m":   [0, 3, 7],
        "7":   [0, 4, 7, 10],
        "m7":  [0, 3, 7, 10],
        "maj7": [0, 4, 7, 11],
    }

    def test_canonical_open_shapes_rank_first(self):
        for (root, quality), expected_voicing in self.EXPECTED_FIRST_VOICINGS.items():
            with self.subTest(chord=root + quality):
                chord = type("Chord", (), {
                    "root": root,
                    "quality": quality,
                    "intervals": self.INTERVALS_BY_QUALITY[quality],
                })()
                voicings = get_all_voicings(chord)
                self.assertTrue(voicings, f"{root}{quality} returned no voicings")
                self.assertEqual(voicings[0], expected_voicing)


if __name__ == "__main__":
    unittest.main(verbosity=2)

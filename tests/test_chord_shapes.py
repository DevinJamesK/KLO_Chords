import unittest

from klo_chord_sample.chord_shapes import (
    shape_pitch_classes,
)
from klo_chord_sample.chords import get_all_voicings, get_diatonic_chords, note_to_pc


class ChordShapeTests(unittest.TestCase):
    def assert_voicings_are_valid(self, root, quality, intervals):
        target = {(note_to_pc(root) + interval) % 12 for interval in intervals}
        for voicing in get_all_voicings(
            type("Chord", (), {
                "root": root,
                "quality": quality,
                "intervals": intervals,
            })()
        ):
            frets = [None] * 6
            for string_idx, fret in voicing:
                frets[string_idx] = fret
            played = shape_pitch_classes(frets)
            self.assertFalse(played - target, (root, quality, voicing, played, target))
            self.assertIn(note_to_pc(root), played)

    def test_common_diatonic_shapes_only_use_chord_tones(self):
        for chord in get_diatonic_chords("C", "Major", include_sevenths=True):
            with self.subTest(chord=chord.root + chord.quality):
                self.assert_voicings_are_valid(
                    chord.root, chord.quality, chord.intervals
                )

    def test_canonical_open_shapes_rank_first(self):
        expected = {
            ("C", "M"): [(1, 3), (2, 2), (3, 0), (4, 1), (5, 0)],
            ("D", "M"): [(2, 0), (3, 2), (4, 3), (5, 2)],
            ("E", "m"): [(0, 0), (1, 2), (2, 2), (3, 0), (4, 0), (5, 0)],
            ("G", "7"): [(0, 3), (1, 2), (2, 0), (3, 0), (4, 0), (5, 1)],
        }
        intervals_by_quality = {
            "M": [0, 4, 7],
            "m": [0, 3, 7],
            "7": [0, 4, 7, 10],
        }
        for key, voicing in expected.items():
            root, quality = key
            with self.subTest(chord=root + quality):
                chord = type("Chord", (), {
                    "root": root,
                    "quality": quality,
                    "intervals": intervals_by_quality[quality],
                })()
                self.assertEqual(get_all_voicings(chord)[0], voicing)


if __name__ == "__main__":
    unittest.main()

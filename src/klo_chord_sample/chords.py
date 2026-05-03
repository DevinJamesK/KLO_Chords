"""
Music theory engine: scales, diatonic triads, chord names, and guitar tab diagrams.

All note math is done in pitch-class (0-11) space.
The chromatic layout is: C=0, C#=1, D=2, D#=3, E=4, F=5, F#=6, G=7, G#=8, A=9, A#=10, B=11
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ── Note names ────────────────────────────────────────────────────────────────

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# Enharmonic alternatives (used for proper chord spelling)
ENHARMONIC = {
    'C#': 'Db', 'D#': 'Eb', 'F#': 'Gb', 'G#': 'Ab', 'A#': 'Bb',
    'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#',
}

# Preferred accidentals for each key signature (for proper spelling)
KEY_PREFERRED_ACCIDENTAL = {
    'F':  'flat', 'Bb': 'flat', 'Eb': 'flat', 'Ab': 'flat',
    'Db': 'flat', 'Gb': 'flat', 'Cb': 'flat',
    'G':  'sharp', 'D':  'sharp', 'A':  'sharp', 'E':  'sharp',
    'B':  'sharp', 'F#': 'sharp', 'C#': 'sharp',
}
KEY_PREFERRED_ACCIDENTAL.setdefault('C', 'flat')


def pc_to_note(pc: int, style: str = "sharp") -> str:
    """Convert a pitch class (0-11) to a note name."""
    name = NOTE_NAMES[pc % 12]
    if style == "flat" and '#' in name:
        return ENHARMONIC[name]
    return name


def note_to_pc(note: str) -> int:
    """Convert a note name (e.g. 'C#', 'Eb') to pitch class 0-11."""
    note = note.strip()
    for pc, name in enumerate(NOTE_NAMES):
        if name == note:
            return pc
        if note in ENHARMONIC and ENHARMONIC[note] == name:
            return pc
    raise ValueError(f"Unknown note: {note}")


def note_name_with_octave(note: str, octave: int = 4) -> str:
    """Return a note name with octave, e.g. 'C4'."""
    return f"{note}{octave}"


# ── Scale definitions ─────────────────────────────────────────────────────────

@dataclass
class ScaleType:
    """A scale pattern defined as semitone intervals from the root."""
    name: str
    intervals: List[int]

    @property
    def degree_names(self) -> List[str]:
        return ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']

    def pitches(self, root: int) -> List[int]:
        return [(root + i) % 12 for i in self.intervals]


SCALE_TYPES = {
    "Major":        ScaleType("Major",        [0, 2, 4, 5, 7, 9, 11]),
    "Natural Minor": ScaleType("Natural Minor", [0, 2, 3, 5, 7, 8, 10]),
    "Harmonic Minor": ScaleType("Harmonic Minor", [0, 2, 3, 5, 7, 8, 11]),
    "Melodic Minor": ScaleType("Melodic Minor",  [0, 2, 3, 5, 7, 9, 11]),
    "Pentatonic Major": ScaleType("Pentatonic Major", [0, 2, 4, 7, 9]),
    "Pentatonic Minor": ScaleType("Pentatonic Minor", [0, 3, 5, 7, 10]),
    "Blues":        ScaleType("Blues",        [0, 3, 5, 6, 7, 10]),
    "Dorian":       ScaleType("Dorian",       [0, 2, 3, 5, 7, 9, 10]),
    "Phrygian":     ScaleType("Phrygian",     [0, 1, 3, 5, 7, 8, 10]),
    "Lydian":       ScaleType("Lydian",       [0, 2, 4, 6, 7, 9, 11]),
    "Mixolydian":   ScaleType("Mixolydian",   [0, 2, 4, 5, 7, 9, 10]),
    "Locrian":      ScaleType("Locrian",      [0, 1, 3, 5, 6, 8, 10]),
}

TRIAD_QUALITIES = {
    "Major":        ["M", "m", "m", "M", "M", "m", "dim"],
    "Natural Minor": ["m", "dim", "M", "m", "m", "M", "M"],
    "Harmonic Minor": ["m", "dim", "aug", "m", "M", "M", "dim"],
    "Melodic Minor":  ["m", "m", "aug", "M", "M", "dim", "dim"],
}

DEFAULT_TRIAD_QUALITIES = ["M", "m", "m", "M", "M", "m", "dim"]


# ── Chord definitions ─────────────────────────────────────────────────────────

@dataclass
class ChordInfo:
    """Information about a single chord."""
    root: str           # Note name of the root, e.g. "C"
    quality: str        # "M", "m", "dim", "aug", "sus2", "sus4", "7", "m7", "maj7", "dim7", "m7b5"
    degree: str         # Roman numeral, e.g. "I", "ii", "V7"
    notes: List[str]    # Note names in the chord
    intervals: List[int]  # Semitone intervals from root


TRIAD_PATTERNS = {
    "M":   [0, 4, 7],
    "m":   [0, 3, 7],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
}

SEVENTH_PATTERNS = {
    "7":    [0, 4, 7, 10],
    "m7":   [0, 3, 7, 10],
    "maj7": [0, 4, 7, 11],
    "dim7": [0, 3, 6, 9],
    "m7b5": [0, 3, 6, 10],
    "mmaj7": [0, 3, 7, 11],
    "aug7": [0, 4, 8, 10],
}


def get_accidental_style(root_note: str) -> str:
    root_clean = root_note.replace('m', '').replace('-', '')
    return KEY_PREFERRED_ACCIDENTAL.get(root_clean, 'sharp')


def _spell_chord(root_pc: int, intervals: List[int], style: str = "sharp") -> List[str]:
    base_letters = ['C', 'C', 'D', 'D', 'E', 'F', 'F', 'G', 'G', 'A', 'A', 'B']
    notes = []
    for interval in intervals:
        pc = (root_pc + interval) % 12
        target_letter = base_letters[pc]
        candidates = []
        for pc_name in NOTE_NAMES:
            if pc_name[0] == target_letter and note_to_pc(pc_name) % 12 == pc:
                candidates.append(pc_name)
        if candidates:
            if style == "sharp":
                preferred = [c for c in candidates if 'b' not in c]
            else:
                preferred = [c for c in candidates if '#' not in c]
            notes.append(preferred[0] if preferred else candidates[0])
        else:
            notes.append(pc_to_note(pc, style))
    return notes


def get_diatonic_chords(root_note: str, scale_name: str = "Major",
                        include_sevenths: bool = False) -> List[ChordInfo]:
    root_pc = note_to_pc(root_note)
    scale = SCALE_TYPES.get(scale_name)
    if not scale:
        raise ValueError(f"Unknown scale type: {scale_name}")

    scale_pitches = scale.pitches(root_pc)
    style = get_accidental_style(root_note)

    qualities = TRIAD_QUALITIES.get(scale_name, DEFAULT_TRIAD_QUALITIES)
    degree_names = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii'] if scale_name != "Major" else \
                   ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']

    chords = []
    for i, scale_pc in enumerate(scale_pitches):
        if i >= len(qualities):
            break
        quality = qualities[i]
        degree = degree_names[i] if i < len(degree_names) else f"^{i+1}"

        if include_sevenths:
            seventh_intervals = []
            for offset in [0, 2, 4, 6]:
                sd = (i + offset) % len(scale_pitches)
                interval = (scale_pitches[sd] - scale_pc) % 12
                seventh_intervals.append(interval)

            chord_root = pc_to_note(scale_pc, style)
            chord_notes = _spell_chord(scale_pc, seventh_intervals, style)

            third = seventh_intervals[1]
            fifth = seventh_intervals[2]
            seventh = seventh_intervals[3]

            if third == 4 and fifth == 7 and seventh == 11:
                q = "maj7"
            elif third == 4 and fifth == 7 and seventh == 10:
                q = "7"
            elif third == 3 and fifth == 7 and seventh == 10:
                q = "m7"
            elif third == 3 and fifth == 6 and seventh == 10:
                q = "m7b5"
            elif third == 3 and fifth == 6 and seventh == 9:
                q = "dim7"
            elif third == 4 and fifth == 8 and seventh == 10:
                q = "aug7"
            elif third == 3 and fifth == 7 and seventh == 11:
                q = "mmaj7"
            else:
                q = f"?7"

            chords.append(ChordInfo(
                root=chord_root, quality=q, degree=degree,
                notes=chord_notes, intervals=seventh_intervals,
            ))
        else:
            triad_intervals = []
            for offset in [0, 2, 4]:
                sd = (i + offset) % len(scale_pitches)
                interval = (scale_pitches[sd] - scale_pc) % 12
                triad_intervals.append(interval)

            chord_root = pc_to_note(scale_pc, style)
            chord_notes = _spell_chord(scale_pc, triad_intervals, style)

            chords.append(ChordInfo(
                root=chord_root, quality=quality, degree=degree,
                notes=chord_notes, intervals=triad_intervals,
            ))

    return chords


def get_scale_notes(root_note: str, scale_name: str = "Major") -> List[str]:
    root_pc = note_to_pc(root_note)
    scale = SCALE_TYPES.get(scale_name)
    if not scale:
        raise ValueError(f"Unknown scale type: {scale_name}")
    scale_pitches = scale.pitches(root_pc)
    style = get_accidental_style(root_note)
    return [pc_to_note(pc, style) for pc in scale_pitches]


# ═══════════════════════════════════════════════════════════════════════════════
# Guitar chord diagrams — multiple voicings per chord
# ═══════════════════════════════════════════════════════════════════════════════

STANDARD_TUNING = [40, 45, 50, 55, 59, 64]
STRING_NAMES = ['E', 'A', 'D', 'G', 'B', 'e']

# Each voicing: list of (string_idx, fret) pairs describing a chord shape.
# string_idx: 0 = high e, 5 = low E
# fret: 0 = open string, None = don't play (muted / not fretted)
#
# Multiple voicings per (root_note, quality) give the user choices.

COMMON_CHORD_SHAPES: Dict[Tuple[str, str], List[List[Tuple[int, int]]]] = {
    # ── C major ────────────────────────────────────────────────────────────
    ("C", "M"): [
        [(5, 3), (4, 2), (3, 0), (2, 1), (1, 0), (0, 0)],           # open C
        [(4, 3), (3, 5), (2, 5), (1, 5), (0, 3)],                    # A-barre fr3
        [(4, 3), (3, 5), (2, 5)],                                     # power chord
        [(5, 3), (4, 2), (3, 0), (2, 1), (1, 0), (0, 3)],           # C/G
    ],
    # ── C minor ───────────────────────────────────────────────────────────
    ("C", "m"): [
        [(5, 3), (4, 3), (3, 0), (2, 1), (1, 0), (0, 0)],           # open Cm
        [(4, 3), (3, 5), (2, 5), (1, 4), (0, 3)],                    # A-barre Cm
    ],
    # ── D major ────────────────────────────────────────────────────────────
    ("D", "M"): [
        [(4, 0), (3, 2), (2, 3), (1, 2), (0, 0)],                    # open D
        [(4, 5), (3, 7), (2, 7), (1, 7), (0, 5)],                    # A-barre fr5
        [(4, 5), (3, 7), (2, 7)],                                     # power chord A5
        [(5, 2), (4, 0), (3, 2), (2, 3), (1, 2), (0, 0)],           # D/F# (bass on E)
    ],
    # ── D minor ───────────────────────────────────────────────────────────
    ("D", "m"): [
        [(4, 0), (3, 2), (2, 3), (1, 1), (0, 0)],                    # open Dm
        [(4, 5), (3, 7), (2, 7), (1, 6), (0, 5)],                    # A-barre Dm
    ],
    # ── E major ────────────────────────────────────────────────────────────
    ("E", "M"): [
        [(5, 0), (4, 2), (3, 2), (2, 1), (1, 0), (0, 0)],           # open E
        [(5, 7), (4, 9), (3, 9), (2, 8), (1, 7), (0, 7)],           # A-barre fr7
        [(5, 0), (4, 2), (3, 2)],                                     # power chord
    ],
    # ── E minor ───────────────────────────────────────────────────────────
    ("E", "m"): [
        [(5, 0), (4, 2), (3, 2), (2, 0), (1, 0), (0, 0)],           # open Em
        [(5, 7), (4, 9), (3, 9), (2, 7), (1, 7), (0, 7)],           # A-barre Em fr7
    ],
    # ── F major ────────────────────────────────────────────────────────────
    ("F", "M"): [
        [(5, 1), (4, 3), (3, 3), (2, 2), (1, 1), (0, 1)],           # E-barre fr1
        [(4, 8), (3, 10), (2, 10), (1, 10), (0, 8)],                 # A-barre fr8
        [(5, 1), (4, 3), (3, 3)],                                     # power chord E1
    ],
    # ── F minor ───────────────────────────────────────────────────────────
    ("F", "m"): [
        [(5, 1), (4, 3), (3, 3), (2, 1), (1, 1), (0, 1)],           # E-barre Fm fr1
    ],
    # ── G major ────────────────────────────────────────────────────────────
    ("G", "M"): [
        [(5, 3), (4, 2), (3, 0), (2, 0), (1, 0), (0, 3)],           # open G
        [(4, 10), (3, 12), (2, 12), (1, 12), (0, 10)],               # A-barre fr10
        [(4, 5), (3, 7), (2, 7)],                                     # power chord A5
        [(5, 3), (4, 2), (3, 0), (2, 0), (1, 0), (0, 3)],           # (same as open)
    ],
    # ── G minor ───────────────────────────────────────────────────────────
    ("G", "m"): [
        [(5, 3), (4, 2), (3, 0), (2, 0), (1, 3), (0, 3)],           # open Gm
        [(4, 10), (3, 12), (2, 12), (1, 11), (0, 10)],               # A-barre Gm
    ],
    # ── A major ────────────────────────────────────────────────────────────
    ("A", "M"): [
        [(4, 0), (3, 2), (2, 2), (1, 2), (0, 0)],                    # open A
        [(5, 5), (4, 7), (3, 7), (2, 6), (1, 5), (0, 5)],           # E-barre fr5
        [(4, 0), (3, 2), (2, 2)],                                     # power chord
        [(5, 0), (4, 0), (3, 2), (2, 2), (1, 2), (0, 0)],           # A/E
    ],
    # ── A minor ───────────────────────────────────────────────────────────
    ("A", "m"): [
        [(4, 0), (3, 2), (2, 2), (1, 0), (0, 0)],                    # open Am
        [(5, 5), (4, 7), (3, 7), (2, 5), (1, 5), (0, 5)],           # E-barre Am fr5
        [(4, 0), (3, 2), (2, 2)],                                     # power chord
    ],
    # ── B major ────────────────────────────────────────────────────────────
    ("B", "M"): [
        [(4, 4), (3, 4), (2, 4), (1, 2), (0, 0)],                    # open-ish B
        [(5, 7), (4, 9), (3, 9), (2, 8), (1, 7), (0, 7)],           # E-barre fr7
        [(4, 2), (3, 4), (2, 4), (1, 4), (0, 2)],                    # A-barre fr2
    ],
    # ── B minor ───────────────────────────────────────────────────────────
    ("B", "m"): [
        [(4, 4), (3, 4), (2, 4), (1, 2), (0, 2)],                   # open Bm shape
        [(5, 7), (4, 9), (3, 9), (2, 7), (1, 7), (0, 7)],           # E-barre Bm fr7
        [(4, 2), (3, 4), (2, 4), (1, 3), (0, 2)],                    # A-barre Bm fr2
    ],

    # ── Dominant 7th chords ──────────────────────────────────────────────
    ("C", "7"):  [
        [(5, 3), (4, 2), (3, 3), (2, 1), (1, 0), (0, 0)],
        [(4, 3), (3, 5), (2, 5), (1, 3), (0, 3)],
    ],
    ("D", "7"):  [
        [(4, 0), (3, 2), (2, 1), (1, 2), (0, 0)],
        [(4, 5), (3, 7), (2, 5), (1, 7), (0, 5)],
    ],
    ("E", "7"):  [
        [(5, 0), (4, 2), (3, 0), (2, 1), (1, 0), (0, 0)],
        [(5, 7), (4, 9), (3, 7), (2, 8), (1, 7), (0, 7)],
    ],
    ("F", "7"):  [
        [(5, 1), (4, 3), (3, 1), (2, 2), (1, 1), (0, 1)],
    ],
    ("G", "7"):  [
        [(5, 3), (4, 2), (3, 0), (2, 0), (1, 0), (0, 1)],
        [(4, 10), (3, 12), (2, 10), (1, 12), (0, 10)],
    ],
    ("A", "7"):  [
        [(4, 0), (3, 2), (2, 0), (1, 2), (0, 0)],
        [(5, 5), (4, 7), (3, 5), (2, 6), (1, 5), (0, 5)],
    ],
    ("B", "7"):  [
        [(4, 4), (3, 4), (2, 2), (1, 2), (0, 2)],
        [(5, 7), (4, 9), (3, 7), (2, 8), (1, 7), (0, 7)],
    ],

    # ── Minor 7th ──────────────────────────────────────────────────────────
    ("C", "m7"): [
        [(5, 3), (4, 3), (3, 3), (2, 1), (1, 0), (0, 0)],
        [(4, 3), (3, 5), (2, 5), (1, 3), (0, 3)],
    ],
    ("D", "m7"): [
        [(4, 0), (3, 2), (2, 1), (1, 1), (0, 0)],
        [(4, 5), (3, 7), (2, 5), (1, 6), (0, 5)],
    ],
    ("E", "m7"): [
        [(5, 0), (4, 2), (3, 0), (2, 0), (1, 0), (0, 0)],
    ],
    ("A", "m7"): [
        [(4, 0), (3, 0), (2, 2), (1, 0), (0, 0)],
        [(5, 5), (4, 7), (3, 5), (2, 5), (1, 5), (0, 5)],
    ],

    # ── Major 7th ──────────────────────────────────────────────────────────
    ("C", "maj7"): [
        [(5, 3), (4, 2), (3, 0), (2, 0), (1, 0), (0, 0)],
        [(4, 3), (3, 5), (2, 5), (1, 4), (0, 3)],
    ],
    ("F", "maj7"): [
        [(5, 1), (4, 3), (3, 2), (2, 2), (1, 1), (0, 0)],
    ],
    ("A", "maj7"): [
        [(4, 0), (3, 1), (2, 2), (1, 2), (0, 0)],
    ],

    # ── Diminished ─────────────────────────────────────────────────────────
    ("B", "dim"): [
        [(4, 3), (3, 4), (2, 2), (1, 0)],
    ],
    ("C", "dim"): [
        [(4, 4), (3, 5), (2, 3), (1, 1)],
    ],
}


def _barre_voicing(root_pc: int, quality: str) -> Optional[List[Tuple[int, int]]]:
    """
    Generate a moveable barre chord voicing.
    String numbering: 0=high_e, 5=low_E. Open pitches: E=4, A=9, D=2, G=7, B=11, e=4.
    """
    e_fret = (root_pc - 4) % 12
    a_fret = (root_pc - 9) % 12

    def e_shape(n):
        if quality == "M":    return [(5,n),(4,n+2),(3,n+2),(2,n+1),(1,n  ),(0,n)]
        if quality == "m":    return [(5,n),(4,n+2),(3,n+2),(2,n  ),(1,n  ),(0,n)]
        if quality == "7":    return [(5,n),(4,n+2),(3,n  ),(2,n+1),(1,n  ),(0,n)]
        if quality == "m7":   return [(5,n),(4,n+2),(3,n  ),(2,n  ),(1,n  ),(0,n)]
        if quality == "maj7": return [(5,n),(4,n+2),(3,n+1),(2,n+1),(1,n  ),(0,n)]
        if quality == "m7b5": return [(5,n),(4,n+1),(3,n  ),(2,n  ),         (0,n)]
        if quality == "dim":  return [(5,n),(4,n+1),         (2,n  ),         (0,n)]
        if quality == "dim7": return [(5,n),(4,n+1),         (2,n  ),(1,n+2),(0,n)]
        if quality == "mmaj7":return [(5,n),(4,n+2),(3,n+1),(2,n  ),(1,n  ),(0,n)]

    def a_shape(n):
        if quality == "M":    return [(4,n),(3,n+2),(2,n+2),(1,n+2),(0,n)]
        if quality == "m":    return [(4,n),(3,n+2),(2,n+2),(1,n+1),(0,n)]
        if quality == "7":    return [(4,n),(3,n+2),(2,n  ),(1,n+2),(0,n)]
        if quality == "m7":   return [(4,n),(3,n+2),(2,n  ),(1,n+1),(0,n)]
        if quality == "maj7": return [(4,n),(3,n+2),(2,n+1),(1,n+2),(0,n)]
        if quality == "m7b5": return [(4,n),(3,n+1),(2,n  ),(1,n+1)]
        if quality == "dim":  return [(4,n),(3,n+1),         (1,n+1)]
        if quality == "dim7" and n >= 1:
                              return [(4,n),(3,n+1),(2,n-1),(1,n+1)]
        if quality == "mmaj7":return [(4,n),(3,n+2),(2,n+1),(1,n+1),(0,n)]

    use_a = (a_fret < e_fret and a_fret <= 9
             and not (quality == "dim7" and a_fret == 0))
    if use_a:
        v = a_shape(a_fret)
        if v is not None:
            return v
    if e_fret <= 9:
        v = e_shape(e_fret)
        if v is not None:
            return v
    if a_fret <= 9:
        v = a_shape(a_fret)
        if v is not None:
            return v
    return None


def _generic_voicing(chord_pcs: set) -> Optional[List[Tuple[int, int]]]:
    open_pc = {5: 4, 4: 9, 3: 2, 2: 7, 1: 11, 0: 4}
    best: List[Tuple[int, int]] = []
    for start in range(13):
        voicing: List[Tuple[int, int]] = []
        for string in [5, 4, 3, 2, 1, 0]:
            for fret in range(start, min(start + 5, 13)):
                if (open_pc[string] + fret) % 12 in chord_pcs:
                    voicing.append((string, fret))
                    break
        if len(voicing) > len(best):
            best = voicing
        if len(best) == 6:
            break
    return best if len(best) >= 3 else None


def get_all_voicings(chord: ChordInfo) -> List[List[Tuple[int, int]]]:
    """
    Return ALL available voicings for a chord as a list of (string, fret) lists.
    The first in the list is the default/preferred.
    """
    voicings = []

    # 1. Look up hand-written shapes (including multiple per key)
    key = (chord.root, chord.quality)
    if key in COMMON_CHORD_SHAPES:
        voicings.extend(COMMON_CHORD_SHAPES[key])

    # 2. Try enharmonic lookup
    alt_root = ENHARMONIC.get(chord.root)
    if alt_root:
        alt_key = (alt_root, chord.quality)
        if alt_key in COMMON_CHORD_SHAPES:
            voicings.extend(COMMON_CHORD_SHAPES[alt_key])

    # 3. Generate barre voicing
    root_pc = note_to_pc(chord.root)
    v = _barre_voicing(root_pc, chord.quality)
    if v is not None and v not in voicings:
        voicings.append(v)

    # 4. Generate generic voicing (last resort)
    chord_pcs = {note_to_pc(n) for n in chord.notes}
    v = _generic_voicing(chord_pcs)
    if v is not None and v not in voicings:
        voicings.append(v)

    return voicings if voicings else []


def get_guitar_diagram(chord: ChordInfo, voicing_idx: int = 0) -> Optional[List[Tuple[int, int]]]:
    """Get a specific guitar chord voicing by index (0 = default)."""
    voicings = get_all_voicings(chord)
    if not voicings:
        return None
    idx = min(voicing_idx, len(voicings) - 1)
    return voicings[idx]


def generate_tab_text(chord: ChordInfo, voicing_idx: int = 0) -> str:
    """Generate a simple ASCII guitar tab for a chord."""
    diagram = get_guitar_diagram(chord, voicing_idx)
    if diagram is None:
        return f"(No tab available for {chord.root}{chord.quality})"

    string_frets = {s: None for s in range(6)}
    for string_idx, fret in diagram:
        string_frets[string_idx] = fret

    lines = []
    for si in range(6):
        sname = STRING_NAMES[5 - si]
        fret = string_frets[5 - si]
        if fret is None:
            lines.append(f"{sname}|--X--|")
        else:
            lines.append(f"{sname}|--{fret}--|")
    return "\n".join(lines)


def format_chord_summary(chord: ChordInfo) -> str:
    """Format a chord for display: e.g. 'C  (C E G)' or 'Dm  (D F A)'"""
    quality_symbol = {
        "M": "", "m": "m", "dim": "°", "aug": "+",
        "7": "7", "m7": "m7", "maj7": "maj7", "dim7": "°7",
        "m7b5": "m7b5", "mmaj7": "mMaj7", "aug7": "+7",
        "sus2": "sus2", "sus4": "sus4",
    }
    q = quality_symbol.get(chord.quality, chord.quality)
    note_str = " ".join(chord.notes)
    return f"{chord.root}{q}  ({note_str})"

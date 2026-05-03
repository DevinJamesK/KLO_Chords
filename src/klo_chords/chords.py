"""
Music theory engine: scales, diatonic triads, chord names, and guitar tab diagrams.

All note math is done in pitch-class (0-11) space.
The chromatic layout is: C=0, C#=1, D=2, D#=3, E=4, F=5, F#=6, G=7, G#=8, A=9, A#=10, B=11
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from klo_chords.chord_shapes import get_ranked_voicings, shape_to_diagram

# ── Note names ────────────────────────────────────────────────────────────────

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

ENHARMONIC = {
    'C#': 'Db', 'D#': 'Eb', 'F#': 'Gb', 'G#': 'Ab', 'A#': 'Bb',
    'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#',
}

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


# ── Scale definitions ─────────────────────────────────────────────────────────

@dataclass
class ScaleType:
    """A scale pattern defined as semitone intervals from the root."""
    name: str
    intervals: List[int]

    def pitches(self, root: int) -> List[int]:
        return [(root + i) % 12 for i in self.intervals]


SCALE_TYPES = {
    "Major":          ScaleType("Major",          [0, 2, 4, 5, 7, 9, 11]),
    "Natural Minor":  ScaleType("Natural Minor",  [0, 2, 3, 5, 7, 8, 10]),
    "Harmonic Minor": ScaleType("Harmonic Minor", [0, 2, 3, 5, 7, 8, 11]),
    "Melodic Minor":  ScaleType("Melodic Minor",  [0, 2, 3, 5, 7, 9, 11]),
    "Pentatonic Major": ScaleType("Pentatonic Major", [0, 2, 4, 7, 9]),
    "Pentatonic Minor": ScaleType("Pentatonic Minor", [0, 3, 5, 7, 10]),
    "Blues":          ScaleType("Blues",          [0, 3, 5, 6, 7, 10]),
    "Dorian":         ScaleType("Dorian",         [0, 2, 3, 5, 7, 9, 10]),
    "Phrygian":       ScaleType("Phrygian",       [0, 1, 3, 5, 7, 8, 10]),
    "Lydian":         ScaleType("Lydian",         [0, 2, 4, 6, 7, 9, 11]),
    "Mixolydian":     ScaleType("Mixolydian",     [0, 2, 4, 5, 7, 9, 10]),
    "Locrian":        ScaleType("Locrian",        [0, 1, 3, 5, 6, 8, 10]),
}

TRIAD_QUALITIES = {
    "Major":         ["M", "m", "m", "M", "M", "m", "dim"],
    "Natural Minor": ["m", "dim", "M", "m", "m", "M", "M"],
    "Harmonic Minor": ["m", "dim", "aug", "m", "M", "M", "dim"],
    "Melodic Minor":  ["m", "m", "aug", "M", "M", "dim", "dim"],
}

DEFAULT_TRIAD_QUALITIES = ["M", "m", "m", "M", "M", "m", "dim"]


# ── Chord definitions ─────────────────────────────────────────────────────────

@dataclass
class ChordInfo:
    """Information about a single chord."""
    root: str
    quality: str
    degree: str
    notes: List[str]
    intervals: List[int]


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _heptatonic_degree_names(scale_name: str) -> List[str]:
    if scale_name == "Major":
        return ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii°']
    return ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii']


def _seventh_quality_from_intervals(intervals: List[int]) -> str:
    third = intervals[1]
    fifth = intervals[2]
    seventh = intervals[3]
    if third == 4 and fifth == 7 and seventh == 11:
        return "maj7"
    if third == 4 and fifth == 7 and seventh == 10:
        return "7"
    if third == 3 and fifth == 7 and seventh == 10:
        return "m7"
    if third == 3 and fifth == 6 and seventh == 10:
        return "m7b5"
    if third == 3 and fifth == 6 and seventh == 9:
        return "dim7"
    if third == 4 and fifth == 8 and seventh == 10:
        return "aug7"
    if third == 3 and fifth == 7 and seventh == 11:
        return "mmaj7"
    return f"?7"


# ── Public API ────────────────────────────────────────────────────────────────

def get_diatonic_chords(root_note: str, scale_name: str = "Major",
                        include_sevenths: bool = False) -> List[ChordInfo]:
    root_pc = note_to_pc(root_note)
    scale = SCALE_TYPES.get(scale_name)
    if not scale:
        raise ValueError(f"Unknown scale type: {scale_name}")

    scale_pitches = scale.pitches(root_pc)
    style = get_accidental_style(root_note)
    qualities = TRIAD_QUALITIES.get(scale_name, DEFAULT_TRIAD_QUALITIES)
    degree_names = _heptatonic_degree_names(scale_name)

    chords = []
    for i, scale_pc in enumerate(scale_pitches):
        if i >= len(qualities):
            break
        degree = degree_names[i] if i < len(degree_names) else f"^{i+1}"
        intervals = []
        for offset in [0, 2, 4, 6] if include_sevenths else [0, 2, 4]:
            sd = (i + offset) % len(scale_pitches)
            interval = (scale_pitches[sd] - scale_pc) % 12
            intervals.append(interval)

        chord_root = pc_to_note(scale_pc, style)
        chord_notes = _spell_chord(scale_pc, intervals, style)

        if include_sevenths:
            quality = _seventh_quality_from_intervals(intervals)
        else:
            quality = qualities[i]

        chords.append(ChordInfo(
            root=chord_root, quality=quality, degree=degree,
            notes=chord_notes, intervals=intervals,
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

def get_all_voicings(chord: ChordInfo) -> List[List[Tuple[int, int]]]:
    """Return validated, playability-ranked voicings for a chord.

    String indexes are low-to-high: 0=low E, 5=high e.
    """
    shapes = get_ranked_voicings(chord.root, chord.quality, chord.intervals)
    return [shape_to_diagram(shape) for shape in shapes]


def get_guitar_diagram(chord: ChordInfo, voicing_idx: int = 0) -> Optional[List[Tuple[int, int]]]:
    """Get a specific guitar chord voicing by index (0 = default)."""
    voicings = get_all_voicings(chord)
    if not voicings:
        return None
    idx = min(voicing_idx, len(voicings) - 1)
    return voicings[idx]

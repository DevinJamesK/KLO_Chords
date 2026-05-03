"""
Music theory engine: scales, diatonic triads, chord names, and guitar tab diagrams.

All note math is done in pitch-class (0-11) space.
The chromatic layout is: C=0, C#=1, D=2, D#=3, E=4, F=5, F#=6, G=7, G#=8, A=9, A#=10, B=11
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from klo_chord_sample.chord_shapes import (
    get_ranked_voicings,
    shape_to_diagram,
)

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

# Runtime chord shapes are loaded and validated in chord_shapes.py.


def get_all_voicings(chord: ChordInfo) -> List[List[Tuple[int, int]]]:
    """
    Return validated, playability-ranked voicings for a chord.

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


def generate_tab_text(chord: ChordInfo, voicing_idx: int = 0) -> str:
    """Generate a simple ASCII guitar tab for a chord."""
    diagram = get_guitar_diagram(chord, voicing_idx)
    if diagram is None:
        return f"(No tab available for {chord.root}{chord.quality})"

    string_frets = {s: None for s in range(6)}
    for string_idx, fret in diagram:
        string_frets[string_idx] = fret

    lines = []
    for string_idx in range(5, -1, -1):
        sname = STRING_NAMES[string_idx]
        fret = string_frets[string_idx]
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

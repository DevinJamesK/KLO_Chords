"""
Music theory engine: scales, diatonic triads, chord names, and guitar tab diagrams.

All note math is done in pitch-class (0-11) space.
The chromatic layout is: C=0, C#=1, D=2, D#=3, E=4, F=5, F#=6, G=7, G#=8, A=9, A#=10, B=11
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import copy

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


@dataclass
class ProgCell:
    """A single cell in the chord progression grid."""
    root: Optional[str] = None
    quality: str = "M"
    inversion: int = 0
    octave: int = 3
    voicing_idx: int = 0

    def is_empty(self) -> bool:
        return self.root is None

    def get_notes(self) -> List[str]:
        """Return the spelled note names for this cell, accounting for inversion."""
        if self.root is None:
            return []
        intervals = QUALITY_INTERVALS.get(self.quality, [0, 4, 7])
        root_pc = note_to_pc(self.root)
        raw_pcs = [(root_pc + i) % 12 for i in intervals]
        # Apply inversion: rotate the chord
        inv = self.inversion % max(1, len(raw_pcs))
        pcs = raw_pcs[inv:] + raw_pcs[:inv]
        style = get_accidental_style(self.root)
        return [pc_to_note(pc, style) for pc in pcs]

    def clear(self):
        self.root = None
        self.quality = "M"
        self.inversion = 0
        self.octave = 3
        self.voicing_idx = 0


QUALITY_INTERVALS = {
    "M":      [0, 4, 7],
    "m":      [0, 3, 7],
    "dim":    [0, 3, 6],
    "aug":    [0, 4, 8],
    "7":      [0, 4, 7, 10],
    "m7":     [0, 3, 7, 10],
    "maj7":   [0, 4, 7, 11],
    "dim7":   [0, 3, 6, 9],
    "m7b5":   [0, 3, 6, 10],
    "mmaj7":  [0, 3, 7, 11],
    "aug7":   [0, 4, 8, 10],
    "sus2":   [0, 2, 7],
    "sus4":   [0, 5, 7],
}


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


# ═══════════════════════════════════════════════════════════════════════════════
# Chord suggestions & palette (customizable progression)
# ═══════════════════════════════════════════════════════════════════════════════

def _parallel_chord(chord: ChordInfo) -> Optional[ChordInfo]:
    """Return the parallel major/minor version of a chord (same root)."""
    parallel_map = {
        "M": "m", "m": "M",
        "7": "m7", "m7": "7",
        "maj7": "m7", "m7": "maj7",
        "dim": "m7b5", "m7b5": "dim",
    }
    new_q = parallel_map.get(chord.quality)
    if new_q is None:
        return None
    return _build_chord_variant(chord.root, new_q)


def _build_chord_variant(root: str, quality: str) -> ChordInfo:
    """Build a ChordInfo from root + quality string, inferring intervals."""
    # Define interval patterns for known qualities
    quality_intervals = {
        "M":      [0, 4, 7],
        "m":      [0, 3, 7],
        "dim":    [0, 3, 6],
        "aug":    [0, 4, 8],
        "7":      [0, 4, 7, 10],
        "m7":     [0, 3, 7, 10],
        "maj7":   [0, 4, 7, 11],
        "dim7":   [0, 3, 6, 9],
        "m7b5":   [0, 3, 6, 10],
        "mmaj7":  [0, 3, 7, 11],
        "aug7":   [0, 4, 8, 10],
        "sus2":   [0, 2, 7],
        "sus4":   [0, 5, 7],
    }
    intervals = quality_intervals.get(quality, [0, 4, 7])
    root_pc = note_to_pc(root)
    style = get_accidental_style(root)
    notes = _spell_chord(root_pc, intervals, style)

    # Pick a suitable degree symbol (roman numeral)
    degree_map_major = {0: "I", 1: "ii", 2: "iii", 3: "IV", 4: "V", 5: "vi", 6: "vii°"}
    # Heuristic: try to find this root in the major scale
    degree = "?"
    for idx, name in enumerate(NOTE_NAMES):
        if note_to_pc(name) == root_pc:
            degree = degree_map_major.get(idx, f"^{idx+1}")
            break

    return ChordInfo(root=root, quality=quality, degree=degree,
                     notes=notes, intervals=intervals)


def get_chord_suggestions(key: str, scale_name: str,
                          chord_list: List[ChordInfo],
                          position: int) -> List[ChordInfo]:
    """Return a list of alternate chords that could replace the chord at *position*.

    Suggestions include parallel chords, functional substitutions,
    common borrowed chords, and secondary dominants.
    """
    if position < 0 or position >= len(chord_list):
        return []
    original = chord_list[position]
    suggestions: List[ChordInfo] = [original]

    # 1. Parallel chord (same root, different quality)
    parallel = _parallel_chord(original)
    if parallel and parallel != original:
        suggestions.append(parallel)

    # 2. Borrowed chords from parallel key (bII, bIII, bVI, bVII)
    root_pc = note_to_pc(original.root)
    scale = SCALE_TYPES.get(scale_name)
    is_major = scale_name in ("Major", "Lydian", "Mixolydian")
    borrowed_pcs = []

    if is_major:
        # Borrow from parallel minor: bIII, iv, bVI, bVII
        borrowed_pcs = [
            (root_pc - 4) % 12,   # bIII
            (root_pc - 5) % 12,   # IVm borrowed
            (root_pc - 8) % 12,   # bVI
            (root_pc - 10) % 12,  # bVII
        ]
    else:
        # Borrow from parallel major
        borrowed_pcs = [
            (root_pc + 4) % 12,   # III
            (root_pc + 5) % 12,   # IV (major)
            (root_pc + 8) % 12,   # VI
            (root_pc + 10) % 12,  # VII
        ]

    style = get_accidental_style(key)
    for bpc in borrowed_pcs:
        bname = pc_to_note(bpc, style)
        if bname == original.root:
            continue
        # Determine quality: if borrowed, it's typically Major for flat chords
        bquality = "M" if is_major else "m"
        suggested = _build_chord_variant(bname, bquality)
        if not any(s.root == suggested.root and s.quality == suggested.quality
                   for s in suggestions):
            suggestions.append(suggested)

    # 3. Add the diatonic chords from other positions as possible substitutions
    for i, ch in enumerate(chord_list):
        if i != position and not any(s.root == ch.root and s.quality == ch.quality
                                      for s in suggestions):
            suggestions.append(ch)

    # 4. Secondary dominant (V of the current chord)
    if len(original.intervals) >= 1:
        third_pc = (note_to_pc(original.root) + original.intervals[1]) % 12
        target = pc_to_note(third_pc, style)
        # Find a chord a 5th above the target
        if scale is not None:
            v_pc = (third_pc + 7) % 12  # A perfect 5th above
            v_name = pc_to_note(v_pc, style)
            v7 = _build_chord_variant(v_name, "7")
            if not any(s.root == v7.root and s.quality == v7.quality
                       for s in suggestions):
                suggestions.append(v7)

    return suggestions

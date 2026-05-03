"""
Guitar chord-shape loading, validation, and ranking.

Internal shape strings use normal guitar order: low E, A, D, G, B, high e.
Example: x32010 is an open C major chord.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from importlib import resources
from typing import Iterable, Optional


NOTE_TO_PC = {
    "C": 0, "B#": 0,
    "C#": 1, "Db": 1,
    "D": 2,
    "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4,
    "F": 5, "E#": 5,
    "F#": 6, "Gb": 6,
    "G": 7,
    "G#": 8, "Ab": 8,
    "A": 9,
    "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11,
}

PC_TO_SHARP = {
    0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
    6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B",
}

OPEN_STRING_PCS = [4, 9, 2, 7, 11, 4]
STRING_COUNT = 6


@dataclass(frozen=True)
class ShapeCandidate:
    frets: tuple[Optional[int], ...]
    fingers: str = ""
    barres: tuple[int, ...] = ()
    sources: tuple[str, ...] = ()
    name: str = ""

    @property
    def fret_string(self) -> str:
        return "".join("x" if fret is None else _fret_to_token(fret)
                       for fret in self.frets)


@dataclass(frozen=True)
class RankedShape:
    shape: ShapeCandidate
    score: int
    missing_pcs: frozenset[int]


def _note_to_pc(note: str) -> int:
    return NOTE_TO_PC[note.strip()]


def _fret_to_token(fret: int) -> str:
    if fret < 10:
        return str(fret)
    return chr(ord("a") + fret - 10)


def _token_to_fret(token: str) -> Optional[int]:
    token = token.strip().lower()
    if token in {"x", "-"}:
        return None
    if token.isdigit():
        return int(token)
    if len(token) == 1 and "a" <= token <= "z":
        return 10 + ord(token) - ord("a")
    raise ValueError(f"Unsupported fret token: {token!r}")


def parse_fret_string(frets: str) -> tuple[Optional[int], ...]:
    """Parse a six-character low-to-high fret string like x32010."""
    parsed = tuple(_token_to_fret(ch) for ch in frets)
    if len(parsed) != STRING_COUNT:
        raise ValueError(f"Expected six strings, got {frets!r}")
    return parsed


def shape_pitch_classes(frets: Iterable[Optional[int]]) -> set[int]:
    pcs = set()
    for string_idx, fret in enumerate(frets):
        if fret is not None:
            pcs.add((OPEN_STRING_PCS[string_idx] + fret) % 12)
    return pcs


def shape_to_diagram(shape: ShapeCandidate) -> list[tuple[int, int]]:
    """Convert a shape to the drawlist format: (string_index, fret)."""
    return [(idx, fret) for idx, fret in enumerate(shape.frets)
            if fret is not None]


def _played_frets(frets: tuple[Optional[int], ...]) -> list[int]:
    return [fret for fret in frets if fret is not None]


def _fretted_notes(frets: tuple[Optional[int], ...]) -> list[int]:
    return [fret for fret in frets if fret is not None and fret > 0]


def _lowest_played_string(frets: tuple[Optional[int], ...]) -> Optional[int]:
    for idx, fret in enumerate(frets):
        if fret is not None:
            return idx
    return None


def _muted_middle_count(frets: tuple[Optional[int], ...]) -> int:
    first = _lowest_played_string(frets)
    if first is None:
        return 0
    last = max(idx for idx, fret in enumerate(frets) if fret is not None)
    return sum(1 for fret in frets[first:last + 1] if fret is None)


def _score_shape(
    shape: ShapeCandidate,
    root_pc: int,
    required_pcs: set[int],
) -> RankedShape:
    pcs = shape_pitch_classes(shape.frets)
    missing = required_pcs - pcs
    played = _played_frets(shape.frets)
    fretted = _fretted_notes(shape.frets)
    lowest = _lowest_played_string(shape.frets)

    score = 0
    score += 18 * len(missing)
    score -= min(len(shape.sources), 3) * 4

    if fretted:
        span = max(fretted) - min(fretted)
        score += span * 5
        score += max(fretted)
    else:
        span = 0

    if any(fret == 0 for fret in played):
        score -= 12
    if lowest is not None:
        bass_pc = (OPEN_STRING_PCS[lowest] + (shape.frets[lowest] or 0)) % 12
        score += -12 if bass_pc == root_pc else 8

    score += _muted_middle_count(shape.frets) * 12
    if len(played) < 4:
        score += 8
    if len(played) > 5:
        score += 3
    if span > 4:
        score += (span - 4) * 12
    if shape.barres:
        score += 2

    return RankedShape(shape=shape, score=score, missing_pcs=frozenset(missing))


@lru_cache(maxsize=1)
def _load_curated_shapes() -> dict[tuple[str, str], tuple[ShapeCandidate, ...]]:
    data_path = resources.files("klo_chord_sample").joinpath(
        "assets", "chords", "guitar_standard.json"
    )
    with data_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    shapes: dict[tuple[str, str], list[ShapeCandidate]] = {}
    for chord in data["chords"]:
        key = (PC_TO_SHARP[_note_to_pc(chord["root"])], chord["quality"])
        for pos in chord["positions"]:
            candidate = ShapeCandidate(
                frets=parse_fret_string(pos["frets"]),
                fingers=pos.get("fingers", ""),
                barres=tuple(pos.get("barres", ())),
                sources=tuple(pos.get("sources", ())),
                name=pos.get("name", ""),
            )
            shapes.setdefault(key, []).append(candidate)
    return {key: tuple(value) for key, value in shapes.items()}


def _movable_shape_candidates(root_pc: int, quality: str) -> list[ShapeCandidate]:
    e_fret = (root_pc - OPEN_STRING_PCS[0]) % 12
    a_fret = (root_pc - OPEN_STRING_PCS[1]) % 12
    shapes: list[ShapeCandidate] = []

    def add(frets: list[Optional[int]], name: str, barres: tuple[int, ...] = ()):
        shapes.append(ShapeCandidate(
            frets=tuple(frets),
            barres=barres,
            sources=("generated-caged",),
            name=name,
        ))

    if 1 <= e_fret <= 9:
        n = e_fret
        if quality == "M":
            add([n, n + 2, n + 2, n + 1, n, n], "E-shape barre", (n,))
        elif quality == "m":
            add([n, n + 2, n + 2, n, n, n], "Em-shape barre", (n,))
        elif quality == "7":
            add([n, n + 2, n, n + 1, n, n], "E7-shape barre", (n,))
        elif quality == "m7":
            add([n, n + 2, n, n, n, n], "Em7-shape barre", (n,))
        elif quality == "maj7":
            add([n, n + 2, n + 1, n + 1, n, n], "Emaj7-shape barre", (n,))

    if 1 <= a_fret <= 9:
        n = a_fret
        if quality == "M":
            add([None, n, n + 2, n + 2, n + 2, n], "A-shape barre", (n,))
        elif quality == "m":
            add([None, n, n + 2, n + 2, n + 1, n], "Am-shape barre", (n,))
        elif quality == "7":
            add([None, n, n + 2, n, n + 2, n], "A7-shape barre", (n,))
        elif quality == "m7":
            add([None, n, n + 2, n, n + 1, n], "Am7-shape barre", (n,))
        elif quality == "maj7":
            add([None, n, n + 2, n + 1, n + 2, n], "Amaj7-shape barre", (n,))

    return shapes


def _generic_candidates(root_pc: int, required_pcs: set[int]) -> list[ShapeCandidate]:
    candidates: list[ShapeCandidate] = []
    for start in range(0, 10):
        frets: list[Optional[int]] = []
        for string_pc in OPEN_STRING_PCS:
            found: Optional[int] = None
            for fret in range(start, min(start + 5, 13)):
                if (string_pc + fret) % 12 in required_pcs:
                    found = fret
                    break
            frets.append(found)
        if sum(fret is not None for fret in frets) >= 3:
            candidates.append(ShapeCandidate(
                frets=tuple(frets),
                sources=("generated-search",),
                name=f"search from fret {start}",
            ))
    return candidates


def get_ranked_voicings(
    root: str,
    quality: str,
    intervals: list[int],
    limit: int = 10,
) -> list[ShapeCandidate]:
    """Return validated, de-duplicated, playability-ranked voicings."""
    root_pc = _note_to_pc(root)
    root_name = PC_TO_SHARP[root_pc]
    required_pcs = {(root_pc + interval) % 12 for interval in intervals}
    candidates = list(_load_curated_shapes().get((root_name, quality), ()))
    candidates.extend(_movable_shape_candidates(root_pc, quality))
    candidates.extend(_generic_candidates(root_pc, required_pcs))

    ranked: list[RankedShape] = []
    seen: set[tuple[Optional[int], ...]] = set()
    for candidate in candidates:
        if candidate.frets in seen:
            continue
        seen.add(candidate.frets)
        played_pcs = shape_pitch_classes(candidate.frets)
        if not played_pcs:
            continue
        if played_pcs - required_pcs:
            continue
        if root_pc not in played_pcs:
            continue
        ranked.append(_score_shape(candidate, root_pc, required_pcs))

    ranked.sort(key=lambda item: (
        len(item.missing_pcs),
        item.score,
        item.shape.fret_string,
    ))
    return [item.shape for item in ranked[:limit]]

"""
Shared fixtures and helpers for the KLO Chords test suite.

Fixtures are organised by domain so each test module pulls in only what it needs.
All fixtures are function-scoped by default (fresh for each test) to avoid
cross-test contamination — which is critical for tests that mutate module-level
state like undo_manager or prefs.

Usage in a test module:
    from klo_chords.core.chords import ProgCell
    def test_example(sample_prog_cell: ProgCell):
        assert sample_prog_cell.root == "C"
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Generator, List

import pytest

from klo_chords.core.chords import (
    ChordInfo,
    ProgCell,
    NOTE_NAMES,
    QUALITY_INTERVALS,
    SCALE_TYPES,
    get_diatonic_chords,
    note_to_pc,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Chord / note fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def c_major_triad() -> ChordInfo:
    """C Major triad: C, E, G."""
    return ChordInfo(
        root="C", quality="M", degree="I",
        notes=["C", "E", "G"], intervals=[0, 4, 7],
    )


@pytest.fixture
def a_minor_triad() -> ChordInfo:
    """A minor triad: A, C, E."""
    return ChordInfo(
        root="A", quality="m", degree="vi",
        notes=["A", "C", "E"], intervals=[0, 3, 7],
    )


@pytest.fixture
def g_dominant_seventh() -> ChordInfo:
    """G dominant 7th: G, B, D, F."""
    return ChordInfo(
        root="G", quality="7", degree="V",
        notes=["G", "B", "D", "F"], intervals=[0, 4, 7, 10],
    )


@pytest.fixture
def d_minor_seventh() -> ChordInfo:
    """D minor 7th: D, F, A, C."""
    return ChordInfo(
        root="D", quality="m7", degree="ii",
        notes=["D", "F", "A", "C"], intervals=[0, 3, 7, 10],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ProgCell fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_prog_cell() -> ProgCell:
    """A filled progression cell: C Major, root position, octave 3."""
    cell = ProgCell()
    cell.root = "C"
    cell.quality = "M"
    cell.rotation = 0
    cell.base_octave = 3
    cell.voicing_idx = 0
    return cell


@pytest.fixture
def empty_prog_cell() -> ProgCell:
    """An empty progression cell."""
    return ProgCell()


@pytest.fixture
def prog_grid_c_major() -> List[ProgCell]:
    """8-cell progression grid filled with C Major diatonic triads."""
    from klo_chords.core.constants import PROG_CELLS_TOTAL
    chords = get_diatonic_chords("C", "Major", include_sevenths=False)
    cells = [ProgCell() for _ in range(PROG_CELLS_TOTAL)]
    for i, chord in enumerate(chords):
        cells[i].root = chord.root
        cells[i].quality = chord.quality
        cells[i].rotation = 0
        cells[i].base_octave = 3
    return cells


# ═══════════════════════════════════════════════════════════════════════════════
# Key / scale fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def all_keys() -> List[str]:
    """All 12 chromatic key names in KLO Chords format."""
    return list(NOTE_NAMES)


@pytest.fixture
def heptatonic_scales() -> List[str]:
    """Scale names that have 7 notes (produce diatonic chords)."""
    return [name for name, scale in SCALE_TYPES.items()
            if len(scale.intervals) == 7]


@pytest.fixture
def all_scales() -> List[str]:
    """All scale names registered in SCALE_TYPES."""
    return list(SCALE_TYPES.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# Temporary file / directory fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def temp_json_file() -> Generator[Path, None, None]:
    """Yield a temporary file path that is cleaned up after the test."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    p = Path(path)
    try:
        yield p
    finally:
        if p.exists():
            p.unlink()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Yield a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


# ═══════════════════════════════════════════════════════════════════════════════
# Quality lookup fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def quality_intervals() -> dict:
    """All known chord quality → interval mappings."""
    return dict(QUALITY_INTERVALS)


# ═══════════════════════════════════════════════════════════════════════════════
# Module-state resets (for tests that mutate global state)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=False)
def reset_undo_manager():
    """Reset the global UndoManager before and after a test.

    Use this fixture sparingly — only in tests that call the real undo manager.
    Mark the test with ``@pytest.mark.usefixtures("reset_undo_manager")``.
    """
    from klo_chords.core.undo_manager import get_undo_manager
    um = get_undo_manager()
    um.clear()
    yield
    um.clear()

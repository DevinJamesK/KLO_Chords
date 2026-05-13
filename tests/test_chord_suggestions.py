"""Tests for klo_chords.core.chord_suggestions — suggestion engine (part 1)."""

from __future__ import annotations

import pytest

from klo_chords.core.chords import ProgCell, note_to_pc, get_diatonic_chords
from klo_chords.core.chord_suggestions import (
    Suggestion,
    get_suggestions,
    get_cell_context,
    _get_borrowed_chords,
    _get_secondary_dominants,
    _get_chromatic_mediants,
    _get_advanced_chords,
    _voice_leading_cost,
    _build_chord_info,
)


@pytest.fixture
def empty_grid() -> list[ProgCell]:
    from klo_chords.core.constants import PROG_CELLS_TOTAL
    return [ProgCell() for _ in range(PROG_CELLS_TOTAL)]


@pytest.fixture
def c_major_grid() -> list[ProgCell]:
    from klo_chords.core.constants import PROG_CELLS_TOTAL
    chords = get_diatonic_chords("C", "Major", include_sevenths=False)
    cells = [ProgCell() for _ in range(PROG_CELLS_TOTAL)]
    for i, c in enumerate(chords):
        cells[i].root = c.root
        cells[i].quality = c.quality
    return cells


class TestSuggestion:
    def test_display_name_simple(self):
        s = Suggestion(root="C", quality="M", category="safe",
                       label="I", voice_leading=0)
        assert "C" in s.display_name()

    def test_display_name_with_resolution(self):
        s = Suggestion(root="G", quality="7", category="secondary_dominant",
                       label="V7", voice_leading=0, resolution_target="C")
        assert "C" in s.display_name()
        assert "G" in s.display_name()


class TestBuildChordInfo:
    def test_major_triad(self):
        ci = _build_chord_info("C", "M")
        assert ci.root == "C"
        assert ci.quality == "M"
        assert ci.notes == ["C", "E", "G"]

    def test_minor_seventh(self):
        ci = _build_chord_info("A", "m7")
        assert ci.root == "A"
        assert ci.quality == "m7"
        assert len(ci.notes) == 4


class TestVoiceLeadingCost:
    def test_no_neighbors_returns_zero(self):
        from klo_chords.core.chords import ChordInfo
        ci = ChordInfo(root="C", quality="M", degree="I",
                       notes=["C", "E", "G"], intervals=[0, 4, 7])
        assert _voice_leading_cost(ci, []) == 0

    def test_same_chord_low_cost(self):
        from klo_chords.core.chords import ChordInfo
        ci = ChordInfo(root="C", quality="M", degree="I",
                       notes=["C", "E", "G"], intervals=[0, 4, 7])
        neighbor = ProgCell()
        neighbor.root = "C"

class TestGetCellContext:
    def test_first_cell_context(self, empty_grid):
        ctx = get_cell_context(empty_grid, 0, "C", "Major")
        assert ctx["left"] is None
        assert ctx["above"] is None

    def test_middle_cell_has_all_neighbors(self, c_major_grid):
        ctx = get_cell_context(c_major_grid, 10, "C", "Major")
        assert ctx["left"] is not None
        assert ctx["right"] is not None

    def test_last_cell_context(self, empty_grid):
        from klo_chords.core.constants import PROG_CELLS_TOTAL
        ctx = get_cell_context(empty_grid, PROG_CELLS_TOTAL - 1, "C", "Major")
        assert ctx["right"] is None
        assert ctx["below"] is None


class TestGetSuggestions:
    def test_returns_suggestions_for_empty_cell(self, c_major_grid):
        suggestions = get_suggestions(c_major_grid, 7, "C", "Major")
        assert len(suggestions) > 0
        safe = [s for s in suggestions if s.category == "safe"]
        assert len(safe) > 0

    def test_suggestions_have_valid_roots(self, c_major_grid):
        suggestions = get_suggestions(c_major_grid, 7, "C", "Major")
        for s in suggestions:
            assert s.root
            assert s.quality
            assert s.category
            pc = note_to_pc(s.root)
            assert 0 <= pc <= 11

    def test_suggestions_sorted_by_category(self, c_major_grid):
        suggestions = get_suggestions(c_major_grid, 7, "C", "Major")
        cat_order = {"safe": 0, "borrowed": 1, "secondary_dominant": 2,
                      "chromatic_mediant": 3, "advanced": 4}
        prev = -1
        for s in suggestions:
            cur = cat_order.get(s.category, 99)
            assert cur >= prev, f"Category {s.category} out of order"
            prev = cur

    def test_sevenths_flag_does_not_crash(self, c_major_grid):
        suggestions = get_suggestions(c_major_grid, 7, "C", "Major",
                                      include_sevenths=True)
        assert len(suggestions) >= 0  # shouldn't crash


class TestBorrowedChords:
    def test_c_major_borrowed(self):
        borrowed = _get_borrowed_chords("C", "Major", "flat")
        assert len(borrowed) > 0
        for pc, quality in borrowed:
            assert 0 <= pc <= 11
            assert quality in ("M", "m")

    def test_a_minor_borrowed(self):
        borrowed = _get_borrowed_chords("A", "Natural Minor", "sharp")
        assert len(borrowed) > 0


class TestSecondaryDominants:
    def test_c_major_sds(self):
        sds = _get_secondary_dominants("C", "Major", "flat")
        assert len(sds) > 0
        for sd in sds:
            assert "root" in sd
            assert "target" in sd

    def test_no_v_of_i(self):
        sds = _get_secondary_dominants("C", "Major", "flat")
        v_roots = {sd["root"] for sd in sds}
        assert "C" not in v_roots


class TestChromaticMediants:
    def test_with_neighbors(self):
        left = ProgCell(); left.root = "C"; left.quality = "M"
        right = ProgCell(); right.root = "G"; right.quality = "M"
        meds = _get_chromatic_mediants(left, right, "C", "flat")
        assert isinstance(meds, list)

    def test_no_neighbors_returns_empty(self):
        meds = _get_chromatic_mediants(None, None, "C", "flat")
        assert meds == []


class TestAdvancedChords:
    def test_c_major_advanced(self):
        adv = _get_advanced_chords("C", "flat")
        assert len(adv) > 0
        labels = {a["label"] for a in adv}
        assert "N (Neapolitan)" in labels
        assert "Ger+6" in labels

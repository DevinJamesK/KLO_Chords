"""
Smart chord suggestion engine.

Given a progression grid and a position, suggests chords based on
neighboring cells, categorized by harmonic function.
"""

from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field

from klo_chords.chords import (
    ChordInfo, ProgCell, NOTE_NAMES, SCALE_TYPES,
    note_to_pc, pc_to_note, get_accidental_style,
    _spell_chord, get_diatonic_chords,
)


# ── Suggestion categories ───────────────────────────────────────────────────────

@dataclass
class Suggestion:
    """A suggested chord for an empty cell."""
    root: str
    quality: str
    category: str       # "safe", "borrowed", "secondary_dominant", "chromatic_mediant", "advanced", "original"
    label: str          # e.g. "V (G)"
    voice_leading: int  # total half-step distance from previous chord
    resolution_target: Optional[str] = None  # e.g. "resolves to IV" for secondary doms
    hidden: bool = False  # for "advanced" chords hidden by default
    is_original: bool = False  # True when this represents the cell's current chord

    def display_name(self) -> str:
        from klo_chords.quality import quality_symbol
        q = quality_symbol(self.quality).strip()
        name = self.root + (" " + q if q else "")
        if self.resolution_target:
            name += f" → {self.resolution_target}"
        return name


# ── Public API ──────────────────────────────────────────────────────────────────

def get_cell_context(
    cells: List[ProgCell],
    idx: int,
    key: str,
    scale_name: str,
    neighbor_flags: Dict[str, bool] = None,
) -> dict:
    """Get context info for a cell: its left/right/up/down neighbors' chords.
    
    Returns dict with:
      - left, right, above, below: Optional[ProgCell]
      - has_left, has_right, etc.: bool
    """
    from klo_chords.state import PROG_COLS
    cols = PROG_COLS
    n = len(cells)
    row = idx // cols
    col = idx % cols

    def _get(i):
        if 0 <= i < n:
            return cells[i]
        return None

    ctx = {
        "left": _get(idx - 1) if col > 0 else None,
        "right": _get(idx + 1) if col < cols - 1 else None,
        "above": _get(idx - cols) if row > 0 else None,
        "below": _get(idx + cols) if row < (n // cols) - 1 else None,
    }
    return ctx


def get_suggestions(
    cells: List[ProgCell],
    idx: int,
    key: str,
    scale_name: str,
    neighbor_flags: Dict[str, bool] = None,
    include_sevenths: bool = False,
) -> List[Suggestion]:
    """Get categorized chord suggestions for the cell at *idx*.
    
    neighbor_flags can include: 'left', 'right', 'above', 'below'
    to control which neighbors influence suggestions.
    Default: left and right only.
    """
    if neighbor_flags is None:
        neighbor_flags = {"left": True, "right": True}

    from klo_chords.state import PROG_COLS
    cols = PROG_COLS
    n = len(cells)
    row = idx // cols
    col = idx % cols

    # Get diatonic chords in the current key for reference
    diatonic_chords = get_diatonic_chords(key, scale_name, include_sevenths=include_sevenths)
    diatonic_root_qual = {(c.root, c.quality) for c in diatonic_chords}
    diatonic_roots = {note_to_pc(c.root) for c in diatonic_chords}

    style = get_accidental_style(key)
    scale = SCALE_TYPES.get(scale_name)
    scale_pcs = set(scale.pitches(note_to_pc(key))) if scale else set()

    # Collect neighbor chords
    def _get_cell(i):
        if 0 <= i < n:
            return cells[i]
        return None

    left_cell = _get_cell(idx - 1) if col > 0 and neighbor_flags.get("left", False) else None
    right_cell = _get_cell(idx + 1) if col < cols - 1 and neighbor_flags.get("right", False) else None
    above_cell = _get_cell(idx - cols) if row > 0 and neighbor_flags.get("above", False) else None
    below_cell = _get_cell(idx + cols) if row < (n // cols) - 1 and neighbor_flags.get("below", False) else None

    neighbors = [c for c in [left_cell, right_cell, above_cell, below_cell] if c is not None and not c.is_empty()]

    suggestions: List[Suggestion] = []

    # ── Safe (diatonic) suggestions ──────────────────────────────────────
    safe = []
    for cd in diatonic_chords:
        suggested = Suggestion(
            root=cd.root, quality=cd.quality,
            category="safe", label=cd.degree,
            voice_leading=_voice_leading_cost(cd, neighbors),
        )
        safe.append(suggested)
    safe.sort(key=lambda s: s.voice_leading)
    suggestions.extend(safe)

    # ── Check if left neighbor is a secondary dominant that wants resolution ──
    if left_cell and not left_cell.is_empty():
        _apply_secondary_dominant_resolution(
            left_cell, cells, idx, key, scale_name, style, neighbors, suggestions
        )

    # ── Borrowed chords (from parallel major/minor) ──────────────────────
    borrowed_chords = _get_borrowed_chords(key, scale_name, style, include_sevenths)
    for b in borrowed_chords:
        if b[0] not in diatonic_roots and (b[0], b[1]) not in diatonic_root_qual:
            suggested = Suggestion(
                root=pc_to_note(b[0], style), quality=b[1],
                category="borrowed", label=_borrowed_label(b[0], key, scale_name),
                voice_leading=_voice_leading_cost(
                    _build_chord_info(pc_to_note(b[0], style), b[1]), neighbors
                ),
            )
            # Avoid duplicates
            if not any(s.root == suggested.root and s.quality == suggested.quality for s in suggestions):
                suggested.voice_leading = _voice_leading_cost(
                    _build_chord_info(suggested.root, suggested.quality), neighbors
                )
                suggestions.append(suggested)

    # ── Secondary dominants ───────────────────────────────────────────────
    sec_doms = _get_secondary_dominants(key, scale_name, style, include_sevenths)
    for sd in sec_doms:
        suggested = Suggestion(
            root=sd["root"], quality=sd["quality"],
            category="secondary_dominant",
            label=f"V7/{sd['target']}",
            voice_leading=_voice_leading_cost(
                _build_chord_info(sd["root"], sd["quality"]), neighbors
            ),
            resolution_target=sd["target"],
        )
        if not any(s.root == suggested.root and s.quality == suggested.quality for s in suggestions):
            suggestions.append(suggested)

    # ── Chromatic mediants ────────────────────────────────────────────────
    chrom_mediants = _get_chromatic_mediants(left_cell, right_cell, key, style)
    for cm in chrom_mediants:
        suggested = Suggestion(
            root=cm["root"], quality=cm["quality"],
            category="chromatic_mediant",
            label=f"chrom. med.",
            voice_leading=_voice_leading_cost(
                _build_chord_info(cm["root"], cm["quality"]), neighbors
            ),
        )
        if not any(s.root == suggested.root and s.quality == suggested.quality for s in suggestions):
            suggestions.append(suggested)

    # ── Advanced (Neapolitan, aug6th) ─────────────────────────────────────
    advanced = _get_advanced_chords(key, style)
    for a in advanced:
        suggested = Suggestion(
            root=a["root"], quality=a["quality"],
            category="advanced",
            label=a["label"],
            voice_leading=_voice_leading_cost(
                _build_chord_info(a["root"], a["quality"]), neighbors
            ),
            hidden=True,
        )
        if not any(s.root == suggested.root and s.quality == suggested.quality for s in suggestions):
            suggestions.append(suggested)

    # Sort within categories by voice leading
    cat_order = {"safe": 0, "borrowed": 1, "secondary_dominant": 2, "chromatic_mediant": 3, "advanced": 4}
    suggestions.sort(key=lambda s: (cat_order.get(s.category, 99), s.voice_leading))

    return suggestions


# ── Voice leading cost ──────────────────────────────────────────────────────────

def _voice_leading_cost(chord: ChordInfo, neighbors: List[ProgCell]) -> int:
    """Compute total voice leading distance (half-steps) from neighbors to chord."""
    if not neighbors:
        return 0  # no constraint
    chord_pcs = set(note_to_pc(n) for n in chord.notes)
    total = 0
    for n in neighbors:
        neighbor_pcs = set(note_to_pc(nn) for nn in n.get_notes())
        # For each note in the neighbor, find closest note in chord
        for npc in neighbor_pcs:
            best = min(abs(npc - cpc) for cpc in chord_pcs)
            total += best
    return total


# ── Helper chord builders ──────────────────────────────────────────────────────

def _build_chord_info(root: str, quality: str) -> ChordInfo:
    """Build a ChordInfo from root + quality."""
    from klo_chords.chords import _build_chord_variant
    return _build_chord_variant(root, quality)


# ── Borrowed chords ────────────────────────────────────────────────────────────

def _get_borrowed_chords(key: str, scale_name: str, style: str,
                         include_sevenths: bool = False) -> List[Tuple[int, str]]:
    """Return (root_pc, quality) for borrowed chords from the parallel key."""
    is_major = scale_name in ("Major", "Lydian", "Mixolydian")
    key_pc = note_to_pc(key)
    borrowed = []

    if is_major:
        # Borrow from parallel minor (natural minor)
        # bIII, iv, bVI, bVII are the most common borrowed chords
        borrowed_pcs = {
            (key_pc + 3) % 12: "M",   # bIII (e.g. Eb in C major)
            (key_pc + 5) % 12: "m",   # iv (e.g. Fm in C major)
            (key_pc + 8) % 12: "M",   # bVI (e.g. Ab in C major)
            (key_pc + 10) % 12: "M",  # bVII (e.g. Bb in C major)
        }
    else:
        # Borrow from parallel major (Picardy third, etc.)
        borrowed_pcs = {
            (key_pc + 4) % 12: "M",   # III (e.g. E in C minor)
            (key_pc + 5) % 12: "M",   # IV (e.g. F in C minor)
            (key_pc + 8) % 12: "M",   # VI (e.g. Ab → A in C minor)
            (key_pc + 10) % 12: "m",  # VII (e.g. Bb → B in C minor)
        }

    for pc, q in borrowed_pcs.items():
        borrowed.append((pc, q))

    return borrowed


def _borrowed_label(root_pc: int, key: str, scale_name: str) -> str:
    """Generate a label for a borrowed chord."""
    style = get_accidental_style(key)
    name = pc_to_note(root_pc, style)
    is_major = scale_name in ("Major", "Lydian", "Mixolydian")
    prefix = "♭" if is_major else "♮"
    return f"{prefix}{name}"


# ── Secondary dominants ────────────────────────────────────────────────────────

def _get_secondary_dominants(key: str, scale_name: str, style: str,
                              include_sevenths: bool = False) -> List[dict]:
    """Return secondary dominant chords.
    
    Each is a dict with 'root', 'quality', 'target' (the chord it resolves to).
    """
    diatonic_chords = get_diatonic_chords(key, scale_name, include_sevenths=include_sevenths)
    results = []

    for dc in diatonic_chords:
        target_root = dc.root
        # The secondary dominant is V of the target
        # V of X = root a P5 above X (7 semitones up)
        target_pc = note_to_pc(target_root)
        sd_root_pc = (target_pc + 7) % 12
        sd_root = pc_to_note(sd_root_pc, style)

        # Use dominant 7th quality
        sd_quality = "7" if include_sevenths else "M"

        # Avoid if it's already diatonic
        if sd_root == key:
            continue  # V of I is just V, not secondary

        results.append({
            "root": sd_root,
            "quality": sd_quality,
            "target": target_root,
        })

    return results


def _apply_secondary_dominant_resolution(
    left_cell: ProgCell,
    cells: List[ProgCell],
    idx: int,
    key: str,
    scale_name: str,
    style: str,
    neighbors: List[ProgCell],
    suggestions: List[Suggestion],
):
    """If the left neighbor is a secondary dominant, push its resolution to
    the top of safe suggestions for this cell."""
    if left_cell.is_empty():
        return
    left_root = left_cell.root
    left_quality = left_cell.quality

    # Check if left is a secondary dominant (dominant 7th quality, root not diatonic)
    if left_quality not in ("7", "M"):
        return

    left_pc = note_to_pc(left_root)
    diatonic_pcs = set(note_to_pc(c.root) for c in get_diatonic_chords(key, scale_name))
    if left_pc in diatonic_pcs:
        return  # it's a regular diatonic chord, not secondary

    # Secondary dominant resolves a P5 down
    target_pc = (left_pc + 5) % 12  # P5 below = P4 up = 5 semitones
    target_name = pc_to_note(target_pc, style)

    # Find or create a safe suggestion for this resolution
    for s in suggestions:
        if s.category == "safe" and note_to_pc(s.root) == target_pc:
            s.voice_leading = -1  # bump to top
            break
    else:
        # Create a safe suggestion for the resolution chord
        quality = "M" if target_name == key else "m"  # rough guess
        # Check diatonic chords
        diatonic = get_diatonic_chords(key, scale_name)
        for dc in diatonic:
            if note_to_pc(dc.root) == target_pc:
                quality = dc.quality
                break
        res_suggestion = Suggestion(
            root=target_name, quality=quality,
            category="safe",
            label=f"{target_name} (resolves V7)",
            voice_leading=-1,  # top priority
        )
        suggestions.insert(0, res_suggestion)


# ── Chromatic mediants ─────────────────────────────────────────────────────────

def _get_chromatic_mediants(
    left_cell: Optional[ProgCell],
    right_cell: Optional[ProgCell],
    key: str,
    style: str,
) -> List[dict]:
    """Return chromatic mediant suggestions.
    
    A chromatic mediant is a chord whose root is a 3rd away (major or minor 3rd)
    from a reference chord, but not diatonic to the key.
    """
    results = []
    refs = []

    if left_cell and not left_cell.is_empty():
        refs.append(left_cell)
    if right_cell and not right_cell.is_empty():
        refs.append(right_cell)

    if not refs:
        return results

    for ref in refs:
        ref_pc = note_to_pc(ref.root)
        # A 3rd away = ±3 or ±4 semitones
        for offset in [3, 4, 8, 9]:  # m3 up, M3 up, m3 down, M3 down
            cand_pc = (ref_pc + offset) % 12
            cand_name = pc_to_note(cand_pc, style)

            # Determine quality: opposite of the reference quality
            ref_is_major = ref.quality in ("M", "7", "maj7")
            cand_quality = "m" if ref_is_major else "M"

            # Skip if it's diatonic to the key (already in safe suggestions)
            diatonic = get_diatonic_chords(key, "Major")
            if any(note_to_pc(c.root) == cand_pc for c in diatonic):
                continue

            results.append({
                "root": cand_name,
                "quality": cand_quality,
            })

    return results


# ── Advanced chords ────────────────────────────────────────────────────────────

def _get_advanced_chords(key: str, style: str) -> List[dict]:
    """Return advanced chord suggestions (Neapolitan, aug6th, etc.)."""
    key_pc = note_to_pc(key)
    results = []

    # Neapolitan chord (bII in first inversion, usually major)
    neap_pc = (key_pc + 1) % 12  # bII
    neap_root = pc_to_note(neap_pc, style)
    results.append({
        "root": neap_root,
        "quality": "M",
        "label": "N (Neapolitan)",
    })

    # German augmented 6th (bVI with augmented 6th)
    ger_pc = (key_pc + 8) % 12  # bVI
    ger_root = pc_to_note(ger_pc, style)
    results.append({
        "root": ger_root,
        "quality": "7",
        "label": "Ger+6",
    })

    # Italian augmented 6th
    it_pc = (key_pc + 8) % 12
    it_root = pc_to_note(it_pc, style)
    results.append({
        "root": it_root,
        "quality": "aug",
        "label": "It+6",
    })

    # French augmented 6th
    fr_pc = (key_pc + 8) % 12
    fr_root = pc_to_note(fr_pc, style)
    results.append({
        "root": fr_root,
        "quality": "7",
        "label": "Fr+6",
    })

    return results

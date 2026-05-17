# Process Log: PySide6 Fretboard Widget Enhancement

## Overview
Enhance `experiments/pyside6_fretboard.py` to match all features from the DPG version (`src/klo_chords/rendering/fretboard.py`).

## Timeline

### 2026-05-16 — Analysis Phase
- **Read DPG fretboard.py (269 lines)**: Full analysis of features:
  - Dual display modes: "fret" (fret numbers, root gold) and "note" (note names, root green)
  - `set_fretboard_mode()` / `get_fretboard_mode()` global state
  - `_centered_text` helper for centered text rendering
  - `_fret_range` to compute start_fret/fret_count from diagram
  - `_draw_fret_dots` shared dot rendering with note name support
  - `draw_mini_fretboard` (115×90 compact preview)
  - `draw_fretboard` (360×220 detail panel)
  - String labels at bottom (E A D G B e)
  - Fret position label when start_fret > 0
  - Open strings: "O" in green, Muted strings: "X" in red
  - Root note: gold in fret mode, green in note mode
  - Uses OPEN_STRING_PCS for note calculation

- **Read PySide6 fretboard.py (140 lines)**: Current features:
  - `STRING_NAMES`, `CHROMATIC`, `OPEN_PITCHES` exports
  - `FretboardWidget` with interactive mouse handling (hover + click toggle)
  - Fret position markers (3,5,7,9,12)
  - String labels on left side
  - Fret numbers at bottom
  - `noteClicked` signal
  - `highlight_pc`, `highlight_notes`, `set_root_pc` for note highlighting
  - `pc_at` for pitch class lookup
  - Minimal demo (C Major pre-loaded)

- **Gap analysis**: What's missing from PySide6 version:
  1. Display mode toggle (fret/note)
  2. `set_chord_shape(diagram, root_pc)` method
  3. `clear_dots()` method
  4. Open string "O" circle display
  5. Muted string "X" display
  6. Dual-mode root highlighting (gold vs green)
  7. Mini fretboard variant
  8. String labels at bottom (currently on left)
  9. Start fret position label
  10. Comprehensive demo with multiple chord presets

- **Checked imports**: `dgen_p1.py` imports `FretboardWidget, CHROMATIC, OPEN_PITCHES`
- **Checked exports**: `pyside6_demo.py` imports same — backward compat required


### 2026-05-16 — Completion & Verification
- **Syntax check**: `py_compile` — PASSED
- **Import check**: All classes (`FretboardWidget`, `MiniFretboardWidget`, `FretboardDemo`) + constants (`STRING_NAMES`, `CHROMATIC`, `OPEN_PITCHES`) import successfully
- **Method check**: All required methods present on both widgets
- **Backward compatibility**: `dgen_p1.py` and `pyside6_demo.py` both parse correctly; all previously exported names still available
- **No issues encountered** — all 8 requirements satisfied

### Final File Summary
- **File**: `experiments/pyside6_fretboard.py` — 711 lines
- **Classes**: `FretboardWidget` (full interactive, ~340 lines), `MiniFretboardWidget` (compact preview, ~118 lines), `FretboardDemo` (test harness, ~131 lines)
- **Exports**: `STRING_NAMES`, `CHROMATIC`, `OPEN_PITCHES`, `FretboardWidget`, `MiniFretboardWidget`, `FretboardDemo`
- **Dependencies**: PySide6 only (no dearpygui)

### Feature Checklist
| # | Requirement | Status |
|---|-------------|--------|
| 1 | Display mode toggle: "fret" / "note" | Done: `set_mode()`/`get_mode()` on both widgets |
| 2 | Open string "O" + muted string "X" | Done: DPG-style rendering above nut |
| 3 | Root highlighting: gold (fret) / green (note) | Done: `set_chord_shape(diagram, root_pc)` |
| 4 | `set_chord_shape()` DPG-compatible format | Done: Accepts `List[Tuple[int, Optional[int]]]` |
| 5 | `clear_dots()` method | Done: On both widgets |
| 6 | Mini fretboard variant | Done: `MiniFretboardWidget` (115x90, non-interactive) |
| 7 | String labels at bottom | Done: E A D G B e labels at bottom |
| 8 | Fret position labels + start-fret indicator | Done: Fret numbers 0-12 at bottom + start-fret label when > 0 |
| 9 | Mouse interaction preserved | Done: Hover ring + click toggle on `_shape` dict |
| 10 | `FretboardDemo` with pre-loaded chords | Done: 8 chord presets (C, Am, G, D, E, F, Em, Dm) |
| 11 | Self-contained (PySide6 only) | Done |
| 12 | Exports `STRING_NAMES, CHROMATIC, OPEN_PITCHES` | Done |

### 2026-05-16 — Bugfixes (post-runtime testing)
- **Fix 1 — Click target area**: `_hit_test` now maps x-position to fret-space centres (where dots are drawn), not fret lines. Uses `int(raw_pos + 0.5)` half-up rounding. Hit margin reduced from `0.45*fs` to `0.35*fs` to create dead zones on fret lines. Hover-ring centre for fret 0 changed from `_ml` to `_ml + fs/2`.
- **Fix 2 — Fret line y-extent**: Lines extend from `_string_y(0) - ss*0.5` to `_string_y(5) + ss*0.5`.
- **Fix 3 — Filled open circles**: `Qt.NoBrush` → `QBrush(QColor(60, 210, 100, 60))`.
- **Fix 4 — Signal connection**: `self.fb.update.connect` → `self.fb.noteClicked.connect(lambda *_: ...)`.
- All fixes verified via offscreen QApplication + hit-test math checks.


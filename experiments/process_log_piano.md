# Process Log: PySide6 Piano Widget Enhancement

**Started**: 2026-05-16

## Step 1: Analyze DPG version (src/klo_chords/rendering/piano.py)
- 168 lines, single and multi-octave pianos
- Features: chord (gold), scale (blue), bass (green) highlighting
- Multi-octave uses MIDI note numbers for tags
- clear_multi_octave_piano for reset

## Step 2: Analyze existing PySide6 version (experiments/pyside6_piano.py)
- 133 lines, already has:
  - 3 octaves (C4-B6)
  - Scroll via _scroll_midi (no wheel event!)
  - highlight_notes() for MIDI notes
  - clear_all() method
  - set_scale_pcs() for scale highlighting
  - noteClicked signal
  - Color constants defined (including _CHB for bass, but unused)
- Missing:
  - Bass note highlighting in paintEvent
  - Octave labels on keys
  - Wheel event for scrolling
  - Comprehensive PianoDemo testing all features

## Step 3: Identify required enhancements
1. Bass note highlighting (_bass_midi attribute + paintEvent logic)
2. Octave labels ("C4", "C5" etc. drawn on C keys)
3. Wheel event handler (wheelEvent)
4. Enhanced PianoDemo with auto-demonstration of all features

## Step 4: Implementation plan
- Add _bass_midi = -1 to __init__
- Add set_bass_note(midi) method
- Modify paintEvent: bass (green) > chord (gold) > scale (blue) > default
- Add wheelEvent to shift _scroll_midi by ±12
- Draw octave labels on C keys at bottom
- Enhance PianoDemo with QTimer cycling through demo states
- Also add black-key bass/chord colors matching DPG

## Step 5: Implementation
- 2026-05-16 — Rewrote `experiments/pyside6_piano.py` (463 lines, up from 133)

### Changes made:
1. **Bass note highlighting** — Added `_bass_midi` state + `set_bass_note(midi)` method. `paintEvent` now checks `midi == _bass_midi and midi in _hl` for green/gold priority matching DPG logic. Black keys get dark green `_CHBB`.
2. **Octave labels** — `paintEvent` draws `C3`, `C4`, `C5`… labels on C keys (right‑aligned, near bottom) using `QPainter.drawText`.
3. **Wheel event** — Added `wheelEvent` handler; scrolls `_scroll_midi` by ±3 white keys (approx half octave) per tick. Widget now sets `Qt.StrongFocus` so it receives wheel events.
4. **Black‑key colour variants** — Added `_CHCB` (dark gold), `_CHSB` (dark blue), `_CHBB` (dark green) matching DPG values exactly.
5. **`clear_all()` now resets bass** — `_bass_midi = -1` is cleared alongside highlights and scale.
6. **Full 88‑key range** — `_MIDI_LO = 21`, `_MIDI_HI = 108` (A0–C8).
7. **Enhanced PianoDemo** — Added:
   - Info label showing current state
   - 8 interactive buttons: C Major Chord, D Minor, F Major, G7, Am, C Major Scale, C Minor Scale, Clear All
   - Auto‑demo timer cycling through 6 different chord+scale+bass combinations every 3 seconds
   - Clicking a key prints (midi, name) to console

## Step 6: Verification
- Syntax check: `py_compile.compile(…, doraise=True)` — **PASSED**
- All required features confirmed present:
  - ✅ Multi-octave (full 88-key range)
  - ✅ Gold/chord, blue/scale, green/bass color coding
  - ✅ Black-key dark color variants
  - ✅ `highlight_notes()` by MIDI note numbers
  - ✅ `set_bass_note()` method
  - ✅ `clear_all()` clears highlights + scale + bass
  - ✅ Octave labels on C keys
  - ✅ Wheel event for scrolling
  - ✅ `noteClicked` signal preserved
  - ✅ PianoDemo tests all features
  - ✅ PySide6 imports only (no dearpygui)
  - ✅ Self-contained, runnable

## Status: COMPLETE

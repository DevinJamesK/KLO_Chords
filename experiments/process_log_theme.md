# Process Log: PySide6 Theme Module

**Task**: Create `experiments/pyside6_theme.py` matching the DPG theme (`src/klo_chords/rendering/theme.py`).

---

## Step 1 — 2026-05-16T00:00:00 — Read DPG Theme
- Read `src/klo_chords/rendering/theme.py` (79 lines).
- Extracted all 16 color constants (RGBA lists).
- Extracted `WAVE_INTERNAL_TO_DISPLAY` and `WAVE_DISPLAY_NAMES`.
- Noted font references: JetBrainsMono-Regular.ttf, DejaVuSans.ttf.

## Step 2 — 2026-05-16T00:01:00 — Plan Color Porting
- All DPG `[R, G, B, A]` lists → `QColor(R, G, B)` (alpha handled separately in QSS where needed).
- COLOR_BG_LIGHT       → `QColor(25, 25, 33)`   — main window background
- COLOR_ACCENT         → `QColor(80, 170, 255)`  — accent blue
- COLOR_ACCENT_GREEN   → `QColor(60, 210, 100)`  — success/green accent
- COLOR_ACCENT_ORANGE  → `QColor(255, 160, 70)`  — warning/orange accent
- COLOR_TEXT           → `QColor(220, 220, 220)`  — primary text
- COLOR_TEXT_DIM       → `QColor(130, 130, 150)`  — dim/secondary text
- COLOR_STRING         → `QColor(190, 170, 130)`  — string color (fretboard)
- COLOR_FRET           → `QColor(70, 70, 80)`     — fret wire color
- COLOR_DOT            → `QColor(210, 190, 150)`  — fret marker dot
- COLOR_ROOT_DOT       → `QColor(255, 210, 50)`   — root note dot
- COLOR_MUTED          → `QColor(200, 60, 60)`    — muted string indicator
- COLOR_OPEN           → `QColor(60, 210, 100)`   — open string indicator
- COLOR_CHORD_BG       → `QColor(28, 28, 36)`    — chord panel background
- COLOR_CHORD_BORDER   → `QColor(59, 59, 64)`    — chord panel border
- COLOR_ACTIVE_SPEAKER → `QColor(0, 230, 80)`    — active speaker indicator
- COLOR_INACTIVE_SPEAKER → `QColor(60, 60, 70)`   — inactive speaker
- COLOR_MIDI_SPEAKER   → `QColor(240, 200, 40)`   — MIDI-only speaker

## Step 3 — 2026-05-16T00:02:00 — Create QSS Stylesheet
- Dark theme QSS with styles for:
  - QMainWindow, QWidget (global defaults)
  - QLabel
  - QComboBox (with drop-down and item view)
  - QSlider (groove, handle, sub-page)
  - QPushButton (normal, hover, pressed, disabled)
  - QCheckBox (indicator states)
  - QTabWidget / QTabBar (tab states)
  - QScrollBar (vertical and horizontal)
  - QGroupBox, QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox
  - QToolTip
  - QMenu (with separator)
- Font families: "JetBrains Mono", "DejaVu Sans Mono", "Consolas", monospace stack.

## Step 4 — 2026-05-16T00:03:00 — Create apply_dark_theme() Helper
- Sets Fusion style.
- Builds QPalette from color constants.
- Applies QSS stylesheet.
- Configures default font.

## Step 5 — 2026-05-16T00:04:00 — Add Theme Preview Demo
- `demo()` function creates a QMainWindow with sample widgets.
- Runs in `if __name__ == "__main__"` block.
- Demonstrates all major widget types.

## Step 6 — 2026-05-16T00:05:00 — Verify Syntax
- [x] Python syntax check passes.
- [x] Module successfully imports.
- [x] All 16 color constants exist as QColor instances.
- [x] WAVE mappings ported.
- [x] Dark palette created.
- [x] QSS stylesheet comprehensive.
- [x] apply_dark_theme() works.
- [x] Demo runs.

## Completion Status: ✅ DONE

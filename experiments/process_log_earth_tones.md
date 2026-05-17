# Earth Tones Theme Update — Process Log

**Goal**: Update all PySide6 widgets in `experiments/` to a lighter warm earth-tone color scheme instead of the current dark/navy theme.

**Started**: 2026-05-17

---

## Step 1 — Process log created (START)
**Timestamp**: 2026-05-17 (start)
**Status**: ✅ Created

---

## Step 2 — Update pyside6_theme.py (PRIMARY)
**Timestamp**: 2026-05-17
**Changes**:
- Added EARTH_* color constants (21 new constants for warm earth tones)
- Added earth_palette() function (warm QPalette)
- Added _QSS_EARTH stylesheet (complete earth-tone QSS)
- Added earth_stylesheet() function
- Added apply_earth_theme() function
- Kept apply_dark_theme() unchanged for backward compatibility
- Kept dark QSS (_QSS) and dark_palette() intact
- Updated demo() to use apply_earth_theme() with EARTH_* colors
- Key earth colors: BG=#F5F0E8, Surface=#EDE4D3, Accent=#C4734F, Text=#4A3728, Dim=#8B7355, Border=#D4C5B0, Selection=#E8A850
**Status**: ✅ Complete

---

## Step 3 — Update pyside6_piano.py
**Timestamp**: 2026-05-17
**Changes**:
- White keys: QColor(255,248,236) warm ivory (#FFF8EC)
- Black keys: QColor(62,46,31) dark warm brown (#3E2E1F)
- Chord highlight: QColor(232,180,80) warm gold/amber (#E8B450)
- Scale highlight: QColor(139,181,160) soft sage (#8BB5A0)
- Bass note: QColor(122,154,85) warm olive green (#7A9A55)
- Key borders: QColor(196,168,130) warm tan (#C4A882)
- Background: QColor(245,240,232) warm cream (#F5F0E8)
- Text: QColor(74,55,40) warm dark brown (#4A3728)
- Demo border updated to warm tan (#C4A882)
- Demo background updated to warm cream (#F5F0E8)
**Status**: ✅ Complete

---

## Step 4 — Update pyside6_fretboard.py
**Timestamp**: 2026-05-17
**Changes**:
- Background (#F5F0E8 warm cream)
- String lines (#8B6F4E warm brown)
- Fret lines (#C4A882 warm tan)
- Nut line (#5A412D darker warm brown)
- Dots: warm gold root (#E8B450), warm tan others (#D4C5B0)
- Note mode root: warm olive green (#7A9A55)
- Hover circle: warm amber (#E8A850)
- Text: (#4A3728), dim text (#8B7355)
- Dot text: warm cream for contrast on dots
- Fret markers: warm tan (#B4A087)
- Demo palette and button styles updated to earth tones
**Status**: ✅ Complete

---

## Step 5 — Update pyside6_chord_box.py
**Timestamp**: 2026-05-17
**Changes**:
- COLOR_ACCENT: terracotta (#C4734F)
- COLOR_CHORD_BG: warm tan card (#EDE4D3)
- COLOR_CHORD_BORDER: warm tan (#D4C5B0)
- COLOR_TEXT: warm dark brown (#4A3728)
- COLOR_TEXT_DIM: warm medium brown (#8B7355)
- COLOR_ACTIVE_SPEAKER: warm amber (#E8A850)
- COLOR_SUGG_BG: warm cream (#F5F0E1)
- Demo stylesheet: all dark colors replaced with warm earth tones
**Status**: ✅ Complete

---

## Step 6 — Update pyside6_demo.py
**Timestamp**: 2026-05-17
**Changes**:
- Main window background: #F5F0E8 (warm cream)
- Text colors: #4A3728 (warm dark brown)
- Dim/section labels: #8B7355 (warm medium brown)
- Scale notes label background: #EDE4D3 (warm tan)
- ComboBox backgrounds: #EDE4D3
- Borders: #D4C5B0 (warm tan)
- Separator: #D4C5B0
- Selection highlight: #E1D6C3
- Main palette (Window, WindowText, Base, Text) updated
**Status**: ✅ Complete

---

## Step 7 — Syntax verification
**Timestamp**: 2026-05-17
**Status**: ✅ Complete — All 5 files pass ast.parse() syntax checks

---

## Summary
All 5 PySide6 widget files in `experiments/` have been updated to a warm earth-tone color scheme:
- `pyside6_theme.py`: Added EARTH_* color constants, earth_palette(), _QSS_EARTH, apply_earth_theme(). Dark theme kept intact.
- `pyside6_piano.py`: White keys → warm ivory, black keys → dark brown, highlights → warm gold/sage.
- `pyside6_fretboard.py`: Background → cream, strings → warm brown, frets → warm tan, dots → gold/green.
- `pyside6_chord_box.py`: Cards → warm tan, borders → warm tan, accent → terracotta.
- `pyside6_demo.py`: Full earth-tone palette applied to combined prototype.

Both dark and earth themes are available:
- `apply_dark_theme(app)` — original dark/navy theme
- `apply_earth_theme(app)` — new warm earth tones

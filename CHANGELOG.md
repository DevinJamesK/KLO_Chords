# Changelog

## [Unreleased]

### Added
- `.vscode/settings.json` — workspace-level Python interpreter, Conda path, and terminal activation settings.
- `environment.yml` — Conda environment definition.
- `chord_degree_dl_N` drawlist for each chord row — renders the Roman numeral degree in a fixed 40 px canvas so all chord boxes align vertically regardless of degree label width.
- Degree drawlist is clickable (bound to the same click handler as the chord box and mini fretboard).

### Changed
- **Font**: Switched from JetBrainsMono-Regular.ttf to Verdana.ttf. The font binary is bundled at `assets/fonts/verdana.ttf`.
- **Asset path resolution**: `_frozen_base()` now returns `None` when not frozen (instead of an empty `Path()` that was truthy), so `_asset_path()` correctly falls through to `importlib.resources.files()` in dev mode. Both `icon_path()` and `font_path()` now return absolute paths that exist.
- **Chord box labels**: Root and quality symbol are now separated by a space (e.g. `"A min"` instead of `"Amin"`) to prevent glyph collision in proportional fonts.
- **Degree column**: Roman numerals (`I`, `ii`, ..., `vii°`) moved from the chord box title into a separate 40 px wide drawlist to the left of each chord box, giving aligned columns.
- **Package data** in `pyproject.toml`: narrowed from `assets/fonts/*.ttf` to only `assets/fonts/verdana.ttf`.
- `pyproject.toml` include-sevenths default remains `false`.

### Removed
- **Dead code** in `chords.py`:
  - `note_name_with_octave()`, `generate_tab_text()`, `format_chord_summary()` — unused functions.
  - `TRIAD_PATTERNS`, `SEVENTH_PATTERNS` — duplicate interval data already covered by `TRIAD_QUALITIES`.
  - `STANDARD_TUNING`, `STRING_NAMES` — only used by the removed functions.
- **Unused imports**:
  - `state.py`: `NOTE_NAMES`, `SCALE_TYPES`, `get_guitar_diagram`.
  - `piano.py`: `COLOR_ACCENT`.
  - `fretboard.py`: `List`, `Optional`, `Tuple` from `typing`.
- **Duplicated constant**: `OPEN_STRING_PCS` in `fretboard.py` — now imports from `chord_shapes.py` (single source of truth for `[4, 9, 2, 7, 11, 4]`).
- `python.conda.enabled` from `.vscode/settings.json` — this is not a real VS Code setting.

### Fixed
- **Icon / font path bug**: `_frozen_base()` returned `Path()` (empty path, truthy in boolean context) when not frozen, causing `_asset_path()` to always take the frozen code branch and return a relative path like `assets\icons\app_icon.ico` that never resolves. Now returns `None` properly.

---
### Added (prior)
- README with project overview, usage instructions, and structure diagram.
- This changelog.
- Local guitar chord-shape data file at `assets/chords/guitar_standard.json`.
- `chord_shapes.py` for loading, validating, de-duplicating, and playability-ranking guitar chord shapes.
- Unit tests that verify returned voicings only contain chord tones and that canonical open shapes rank first.
- Conda/Miniforge setup instructions in the README.

### Changed
- Refactored monolithic `gui.py` into separate modules:
  - `theme.py` - color palette, font path
  - `quality.py` - chord quality symbol/spelled formatting
  - `chord_box.py` - chord name tile rendering
  - `fretboard.py` - mini and large fretboard drawing
  - `piano.py` - piano keyboard drawing and highlighting
  - `state.py` - global state, all callbacks, chord list management
- `gui.py` now only handles UI layout construction and the main loop.
- Chord quality notation made consistent:
  - Short form: "C", "Dmin", "Emin7", "Fmaj7", "G7", etc.
  - Spelled form: "Major", "minor", "minor 7", "major 7", "7", etc.
- Scale notes text now properly centered via horizontal group + spacer.
- Chord boxes narrowed from 200px to 155px and centered in the left panel.
- Top margin of chord list adjusted to align with the 0-fret on mini fretboards.
- Quality detail colors changed from `COLOR_ACCENT_ORANGE` to `COLOR_ACCENT` for visual consistency.
- Guitar voicings now use normal low-to-high string order: `E A D G B e`.
- `get_all_voicings()` now uses the validated local chord-shape pipeline instead of the old hand-written runtime table.
- Package data now includes bundled chord JSON files.
- README dependency note now matches `pyproject.toml` by requiring Python 3.11+.

### Fixed
- Syntax error on line 568 (stray character) resolved during refactor.
- `m7` quality was incorrectly mapping to `"7"` in chord labels; now correctly shows `"min7"`.
- Removed invalid hard-coded guitar voicings from runtime use.
- Root highlighting on fretboard diagrams now checks the actual played note instead of assuming one string is the root.
- README and changelog mojibake in punctuation and tree-drawing characters.

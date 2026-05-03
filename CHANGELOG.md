# Changelog

## [Unreleased]

### Added
- GitHub Actions build workflow (`.github/workflows/build.yml`) — produces standalone executables for Windows (`.exe`) and macOS (`.app`) on every push to `main`.
- App icon (`assets/icons/app_icon.ico`) displayed in the OS title bar via `dpg.set_viewport_large_icon` and `dpg.set_viewport_small_icon`.
- `icon_path()` helper in `theme.py` resolves the icon for both frozen (PyInstaller) and dev-mode runs.
- Download section in README linking to GitHub Actions artifacts.

### Changed
- Renamed project from `KLO_Chord_Sample` / `klo_chord_sample` to `KLO_Chords` / `klo_chords` across all source files, config, and documentation.
- Package name changed from `klo-chord-sample` to `klo-chords` in `pyproject.toml`.
- Conda environment name updated to `klo-chords` in README setup instructions.
- Project structure diagram in README updated to reflect new package directory and icons asset.

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

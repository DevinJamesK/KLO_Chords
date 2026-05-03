# Changelog

## [Unreleased]

### Added
- README with project overview, usage instructions, and structure diagram.
- This changelog.

### Changed
- Refactored monolithic `gui.py` into separate modules:
  - `theme.py` — color palette, font path
  - `quality.py` — chord quality symbol/spelled formatting
  - `chord_box.py` — chord name tile rendering
  - `fretboard.py` — mini and large fretboard drawing
  - `piano.py` — piano keyboard drawing and highlighting
  - `state.py` — global state, all callbacks, chord list management
- `gui.py` now only handles UI layout construction and the main loop.
- Chord quality notation made consistent:
  - Short form: "C", "Dmin", "Emin7", "Fmaj7", "G7", etc.
  - Spelled form: "Major", "minor", "minor 7", "major 7", "7", etc.
- Scale notes text now properly centered via horizontal group + spacer.
- Chord boxes narrowed from 200px to 155px and centered in the left panel.
- Top margin of chord list adjusted to align with the 0-fret on mini fretboards.
- Quality detail colors changed from `COLOR_ACCENT_ORANGE` to `COLOR_ACCENT` for visual consistency.

### Fixed
- Syntax error on line 568 (stray character) resolved during refactor.
- `m7` quality was incorrectly mapping to `"7"` in chord labels; now correctly shows `"min7"`.

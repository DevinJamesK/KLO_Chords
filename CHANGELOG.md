# Changelog

## [0.4.0] - 2026-05-04

### Added
- **Mute/Unmute** — press `ESC` to toggle mute on/off. Volume slider turns red when muted; slider interaction auto-unmutes.
- **Stop playback** — press `Spacebar` to stop any currently playing chord.
- **Fretboard note-name mode** — new "Show Note Names" checkbox on the Chord Detail panel toggles between fret numbers (default) and actual note names inside the fretboard dots. Root notes are green in note-name mode.
- **Multi-octave piano for progression tab** — 2-octave piano keyboard in the progression cell detail panel, dynamically centered on the selected cell's octave.
- **Wave preview canvas** — small waveform preview in the toolbar that updates when the wave type changes (Triangle / Sine / Sawtooth).
- **Progression fill from selected cell** — "Fill Chords" now starts from the currently selected cell (or column 0) and fills right→down like reading.
- **Clear All button** — red "Clear All" button on the progression tab to reset all grid cells at once.
- **`ProgCell` dataclass** — moved from `state.py` to `chords.py` with `get_notes()` method that accounts for inversion, and `clear()` convenience method.
- **`QUALITY_INTERVALS` dict** — centralized interval definitions for all supported chord qualities (`M`, `m`, `dim`, `aug`, `7`, `m7`, `maj7`, `dim7`, `m7b5`, `mmaj7`, `aug7`, `sus2`, `sus4`).
- **`font_path_fallback()`** — returns path to JetBrains Mono for potential use as a fallback font.

### Changed
- **Viewport height** — reduced from 1080 to 960 for a more compact default window.
- **Chord box dimensions** — narrowed from 154→140 px, height 89→90 px for a tighter chord list layout.
- **Chord tab layout** — key/scale/7th toggle moved into a single top row above the two-panel layout (left: chord list, right: detail panel). Removed inner "Key & Scale" and "Scale Notes" child window sections.
- **Fretboard centering** — both mini and large fretboards now center horizontally using dynamic string spacing. Start-fret labels rendered in yellow (`[255, 230, 80]`) instead of dim text.
- **Voicing label** — padded to constant 8-character width to prevent layout shifts (e.g. `"1/3"` vs `"1/10"`).
- **Volume slider** — changed from float 0.0-1.0 to integer 0-100 with percentage-based internal conversion.
- **Wave type combo** — now displays user-friendly names ("Triangle", "Sine", "Sawtooth") instead of internal keys; both toolbar and Sound Settings combos stay in sync.
- **Speaker indicators** — removed blinking speaker dots from both chord list and progression cells. Play bars remain as the sole visual playback indicator.
- **Progression tab toolbar** — labels simplified ("Key" instead of "Key  ", "Include 7th" instead of "7th Chords"), combos resized to match chord tab (50px key, 150px scale).
- **Sound Settings tab** — removed auto-play help text, simplified checkbox labels, added separator pipes for visual grouping.
- **Toolbar layout** — volume label text no longer accent-colored, legato label simplified, visual separators (`|`) between control groups.

### Removed
- **Speaker indicator dots** — `spkr_dot_*` and `prog_spkr_dot_*` draw calls removed from `chord_box.py` and `state.py`. Related `_refresh_speaker_indicators()` logic simplified to only handle play bars.
- **`on_sound_mode_change` callback** — consolidated into `on_wave_type_change` which handles both display and internal names.

### Fixed
- **Progression fill only filled first row** — `on_prog_fill()` now fills from the selected cell across all 32 cells (8 cols × 4 rows) instead of only the first 8.
- **Progression piano centered on wrong octave** — `_update_prog_piano()` now dynamically rebuilds the canvas centered on the cell's octave, so chords play and display in the middle of the keyboard.

---

## [0.3.2] - 2026-05-03

### Changed
- **Base font size** — increased from 16 to 20 for improved readability across the entire app
- **All `draw_text` font sizes** — increased proportionally in `chord_box.py`, `fretboard.py`, and `state.py` (title: 20→24, notes: 16→18, grid cell text: 11-14→13-16, fretboard text: 12→14+)

### Fixed
- **Progression tab key/scale chooser off-center** — added proper centering calculation with `_CHOOSER_PAD`
- **Progression grid slightly right** — removed arbitrary `-14` fudge factor from `GRID_PAD` calculation, removed trailing spacer after last cell in each row
- **Cell details too close to left wall** — added `24px` left padding to all detail controls (Selected, Root, Quality, Inversion, Octave, Notes)
- **Piano slightly left on progression tab** — removed arbitrary `-60` fudge factor from `_piano_pad` calculation

## [0.3.1] - 2026-05-03

### Added
- **8×4 progression grid** — clickable cells with degree, name, and notes display
- **ProgCell dataclass** — stores root, quality, and inversion per progression cell
- **Cell detail panel** — root/quality/inversion combos for editing any progression cell
- **draw_prog_cell()** — compact grid cell renderer in `chord_box.py` with speaker dot and play bar
- **Progression tab keyboard support** — keys 1-8 select/play cells from the first row
- **Tab-aware keyboard routing** — number keys only work on the active tab
- **Tab-switch sound stop** — sound stops when switching between tabs

### Changed
- **Progression tab** — redesigned from horizontal slot list to 8×4 grid with edit controls
- **Sound playback for progression cells** — uses cell's stored notes directly (no auto voice-leading)
- **"Press 1-8" text** — centered in left panel of chord tab
- **"Include 7th chords" checkbox** — aligned with combo boxes above using spacer
- **Sound settings layout** — consistent margins and indentation throughout
- **Speaker indicators** — now also handle progression cell dots and play bars

## [0.3.0] - 2026-05-03

### Added
- **Streaming sound engine** — continuous `sounddevice` callback generates audio with numpy vectorized operations. No file I/O, glitch-free playback.
- **Playable chords** — selecting a chord automatically plays its notes via the sound engine.
- **Number key shortcuts (1-8)** — press 1-8 to select and play the corresponding diatonic chord.
- **Toggle and One-Shot playback modes** — toggle chords on/off or play a ~1s burst.
- **Legato mode** — notes shared between consecutive chords are held, only differing notes re-strike.
- **Velocity controls** — random velocity per note with configurable min/max range for natural dynamics.
- **Waveform selection** — triangle (default), sine, or sawtooth waveform.
- **Base octave slider** — shift chord voicings up or down.
- **Sound settings tab** — central panel for all audio configuration (enable, wave, velocity, playback mode, base octave, legato).
- **Toolbar** — persistent volume slider, wave type combo, and legato toggle visible on every tab.
- **Piano keyboard highlighting** — chord notes in gold, scale-only notes in blue, bass note in green.
- **Inversion display** — shows inversion name (Root Position / 1st / 2nd / 3rd) and sounding note names below the piano keyboard.
- **Speaker indicator dots** — small animated dots next to each chord row that blink when that chord is sounding.
- **Play bar indicator** — thin colored bar at the bottom of the active chord box for extra visual feedback.
- **Chord suggestions engine** — `get_chord_suggestions()` in `chords.py` returns parallel chords, borrowed chords, and secondary dominants for progression building.
- **Green key + inversion update every frame** — bass note and inversion info appear immediately when sound starts and disappear instantly when sound stops.

### Changed
- **Dependencies** — added `sounddevice` and `numpy` to `pyproject.toml`, `requirements.txt`, and `environment.yml`.
- **Voice leading** — MIDI note computation with `_voice_chord()`, `_first_voicing()`, `_fix_spacing()`, and `_anti_drift()` ensures smooth transitions between chords.
- **`update_piano_keys()`** — now accepts `bass_pc` parameter for green bass-note highlighting.
- **Main loop** — `_refresh_speaker_indicators()` now called directly in the render loop instead of via recursive frame callbacks.
- **Chord detail panel** — `_update_inversion_display()` moved entirely to the frame callback, removed from `_update_selected_chord()` to avoid race conditions with sound start.

### Fixed
- **Speaker dots invisible** — added `COLOR_INACTIVE_SPEAKER` (dim gray) so dots are always visible.
- **Mode switching leaves notes stuck** — `set_playback_mode()` now calls `release_all()` and clears note history.
- **Green key / inversion lag** — removed `% 5` frame gate so inversion and bass key update every frame.
- **Stray `c` file** — removed orphan file from project root.

## [0.2.0] - 2026-05-03

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

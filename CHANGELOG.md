# Changelog

## [0.5.4] - 2026-05-08

### Changed
- **Crisp text on Retina displays** — font atlas is now baked at 2× on macOS (`_DISPLAY_SCALE = 2.0`) and the global font scale is halved, eliminating pixelation on HiDPI screens. Non-macOS builds are unaffected.
- **Widget font size reduced to 16 px** — matches the chord-name text drawn inside progression grid cells.
- **Toolbar spacing tightened** — inter-element spacers reduced from 20 px to 8 px; the opening left indent is unchanged.

## [0.5.3] - 2026-05-08

### Added
- **Guitar chord shape audit** — new `tests/test_chord_shapes.py` suite with 1,516 subtests:
  - `CuratedShapeAuditTests` — every entry in `guitar_standard.json` is validated for chord-tone purity and root presence.
  - `DiatonicVoicingCoverageTests` — all 12 keys × 9 heptatonic scales × triads and 7ths confirmed to have at least one valid voicing; catches any `?` quality regressions.
  - `CanonicalShapeRankingTests` — canonical open shapes (C, D, Em, G7, …) must rank first.
- **Console logging for Chord tab** — selecting or playing a diatonic chord now prints a fixed-column log line alongside the existing Progression tab logging.
- **Sub oscillator note in log** — all event log lines now include a `sub:` column showing the sub oscillator MIDI note (e.g. `sub:C3`) when enabled, or `sub:--` when off.

### Fixed
- **Two bad curated guitar shapes** — `B dim x2313x` had G# (not in B dim); corrected to `x2343x`. `C dim x3424x` had A (not in C dim); corrected to `x3454x`. Both were silently rejected by the validator at runtime; the JSON data now matches what the validator accepts.

### Changed
- **Unified log format** — all play-event log lines (`[chord N]`, `[cell N]`) share a fixed-column formatter: tag, degree, chord name, context (oct/rot), note names, MIDI names, sub note. Fields no longer shift between chord-tab and progression-tab events.

## [0.5.2] - 2026-05-08

### Added
- **Augmented major 7th chord** (`+Maj7`) — Harmonic Minor iii and Melodic Minor iii were displaying as `?7`; now correctly named and fully supported in the quality symbol and spelled-out name tables.
- **Modal scale triad qualities** — Dorian, Phrygian, Lydian, Mixolydian, and Locrian now have correct diatonic triad quality tables instead of falling back to the Major scale pattern. Affected degrees: e.g. Dorian i (was Major, now minor), Mixolydian iii (was minor, now diminished), Locrian VII (was diminished, now Major), etc.

### Changed
- **Progression grid expanded to 8×4** — grid is now 8 columns × 4 rows (32 cells, up from 7×4 / 28 cells). Keyboard shortcuts updated to match: `1–8`, `Q–I`, `A–K`, `Z–,`.
- **Pentatonic and blues scales show no diatonic chords** — stacking scale degrees across a 5- or 6-note scale produces non-standard intervals that don't correspond to real chords. The chord list now shows an informational message directing users to the Progression tab instead.
- **"Include 7th" disabled for non-heptatonic scales** — the checkbox is greyed out when a pentatonic or blues scale is selected.
- **Scale change stops audio** — switching scales in the Chord tab now stops any currently playing sound.

## [0.5.1] - 2026-05-06

### Changed
- **Inversion system simplified** — `ProgCell` now uses a single `rotation` field (replacing separate `inversion` + `octave`). Rotation tracks cumulative inversion steps from root position; `rotation % num_notes` gives inversion index, `rotation // num_notes` gives octave offset. Octave wraps naturally as you cycle through inversions.
- **Inversion anchored to chord root** — `_stack_root_position` now anchors the bass note to the chord's actual root pitch class (e.g., F for F Major) instead of always C. Fixes inversion ordering for non-C roots.
- **MIDI range clamping** — Inversion/rotation steps that would push notes outside MIDI range (0–127) are now prevented with automatic rollback.

### Added
- **Audio quality presets** — new "Audio Quality" combo in the Sound Settings tab with three modes:
  - **Smooth** — polyBLEP anti-aliasing on triangle and sawtooth waves + soft tanh clipper + larger 1024-sample buffer for fewer dropouts
  - **Responsive** — standard 512-sample buffer with soft tanh clipper (no polyBLEP)
  - **Legacy** — original hard peak limiter, standard buffer
- **Persistent preferences** — new `prefs.py` module saves sound settings, keybind display, and fretboard note-name mode to `preferences.json` (platform-native paths: `~/Library/Application Support/KLO_Chords/` on macOS, `%LOCALAPPDATA%/KLO_Chords/` on Windows, `~/.local/share/KLO_Chords/` on Linux). Settings persist across restarts and include schema versioning for future migrations.

### Fixed
- **F Major inversion ordering** — anchor fix ensures correct bass note ordering for chords rooted on F and other notes where C-anchoring produced wrong octave placement.
- **Octave search range** — expanded from `range(0,9)` to `range(0,11)` to correctly find MIDI placements at extreme pitches.
- **Sound stops on octave change** — removed erroneous `stop_current()` call from octave callbacks; sound now continues playing when adjusting base octave.

## [0.5.0] - 2026-05-05

### Added
- **Chord suggestions panel** — select any progression cell (empty or non-empty) to see categorized suggestions: safe (diatonic), borrowed chords, secondary dominants, chromatic mediants, and advanced chords. Click any suggestion to instantly apply it. `chord_suggestions.py` provides the full suggestion engine with voice-leading-based ranking.
- **Multi-select in progression grid** — Shift+click to select a range of cells, Ctrl/Cmd+click to toggle individual cell selection. Copy (Ctrl+C) and Paste (Ctrl+V) with multiple paste modes:
  - **Replace mode** — overwrites cells starting at the paste position
  - **Insert mode** — shifts existing cells right to make room
  - **Swap mode** — exchanges clipboard contents with target cells
  - **Preserve Shape paste** — keeps the original 2D row/column layout of copied cells
- **Undo/Redo manager** — `undo_manager.py` with full command-pattern undo/redo for all progression grid mutations (paste, insert, replace, swap, delete, fill, suggestions, move). Supports batched operations and unlimited history up to 100 steps.
- **Delete selected cells** — press Delete to clear all multi-selected cells at once.
- **Move selection up/down** — Ctrl+Up / Ctrl+Down moves multi-selected cells one row up or down, swapping with adjacent cells.
- **Dynamic roman numerals** — each progression cell now computes its roman numeral from the cell's actual root vs the current key/scale (letter-name-based). Non-diatonic chords get ♭/♯ prefixes (e.g. ♭VII, ♯IV).
- **Progression keyboard shortcuts** — map all 28 cells to keys: 1-7 (row 0), Q-U (row 1), A-J (row 2), Z-M (row 3). Hold Ctrl while pressing the key to select without triggering sound.
- **Arrow key navigation in progression tab** — Left/Right = cycle inversion of selected cell, Up/Down = cycle quality of selected cell.
- **Cross-platform modifier key module** — `dpg_keyboard.py` provides `ctrl_is_down()`, `shift_is_down()`, `cmd_is_down()`, and `toggle_is_down()` (platform-native: Cmd on macOS, Ctrl on Windows/Linux) for modifier+click operations. Polled every frame.
- **Launcher scripts** — `run.sh` (macOS/Linux) and `run.bat` (Windows) with automatic Conda env creation, dependency installation, and editable package install — one-command launch on any platform.
- **Mute/Unmute** — press `ESC` to toggle mute on/off. Volume slider turns red when muted; slider interaction auto-unmutes.
- **Stop playback** — press `Spacebar` to stop any currently playing chord.
- **Fretboard note-name mode** — new "Show Note Names" checkbox on the Chord Detail panel toggles between fret numbers (default) and actual note names inside the fretboard dots. Root notes are green in note-name mode.

### Changed
- **Progression tab layout** — added suggestions panel below the grid; Paste Mode and Paste Shape combos moved to their own row below Key/Scale; cell detail panel relocated directly below the grid row.
- **Roman numeral display** — degree is now computed per-cell (`get_degree_for_root()`) rather than derived from column position, accurately reflecting non-diatonic chords. Completely rewritten to use letter-name matching instead of pitch-distance tie-breaking.
- **Mini fretboard proportions** — tighter string spacing, removed numbers from dots, shrink dot radius 6→4.
- **Big fretboard canvas** — match canvas width to 360px, snap low E string to x=8.
- **Fretboard nut bar color** — now renders as grey-yellow [190,185,140] on both mini and large fretboards when `start_fret==0`.
- **Fretboard dot text readability** — dark text on gold root dots for clear contrast.
- **Progression keyboard** — 7-column grid (was 8-column).

### Fixed
- **macOS transparent window crash** — `dpg_keyboard.py` now uses DPG key codes 527/663 for Cmd press/release on macOS instead of `ctypes.windll.user32` (Win32 API which does not exist on macOS).
- **Platform-native modifier+click** — `toggle_is_down()` returns Cmd on macOS (Ctrl is right-click on Mac) and Ctrl on Windows/Linux for multi-select toggle operations.
- **Progression piano range** — the multi-octave piano dynamically shifts its displayed range so all sounding notes are always visible, regardless of the chord's octave.
- **Fretboard leftmost dot clipping** — widen mini fretboard canvas to 390px and shift `x_start` to 12 (subsequently kept at 360px width with `x_start=12`).
- **Fretboard X/O overlap with nut** — pushed text above nut on mini (y0→18) and large (`y_start`→24) fretboards.
- **Large fretboard X/O clipping** — adjusted canvas height and `y_start` so X/O text isn't clipped.
- **Speaker indicator crash on macOS** — catch generic `Exception` instead of `SystemError` in speaker indicator refresh to avoid crashes on non-Windows platforms.
- **Legato mode stale voice detection** — exclude released (fading-out) voices from the "already playing" check so notes are properly re-triggered during legato transitions.
- **Normal click deselects multi-selection** — clicking a single cell without modifiers clears any existing multi-selection before selecting the clicked cell.
- **Bb in C Major roman numeral** — now correctly shows ♭vii° (was showing ♯vi due to ambiguous distance tie-breaking).
- **Avoid global variable in click handler** — `on_prog_cell_click` uses getter/setter helpers instead of direct global access.

---

## [0.4.0] - 2026-05-04

### Added
- **Mute/Unmute** — press `ESC` to toggle mute on/off. Volume slider turns red when muted; slider interaction auto-unmutes.
- **Stop playback** — press `Spacebar` to stop any currently playing chord.
- **Fretboard note-name mode** — new "Show Note Names" checkbox on the Chord Detail panel toggles between fret numbers (default) and actual note names inside the fretboard dots. Root notes are green in note-name mode.
- **Multi-octave piano for progression tab** — 2-octave piano keyboard in the progression cell detail panel, dynamically centered on the selected cell's octave.
- **Wave preview canvas** — small waveform preview in the toolbar that updates when the wave type changes (Triangle / Sine / Sawtooth).
- **Progression fill from selected cell** — "Fill Chords" now starts from the currently selected cell (or column 0) and fills right→down.
- **Clear All button** — red "Clear All" button on the progression tab to reset all grid cells at once.
- **`ProgCell` dataclass** — moved from `state.py` to `chords.py` with `get_notes()` method accounting for inversion, and `clear()` convenience method.
- **`QUALITY_INTERVALS` dict** — centralized interval definitions for all supported chord qualities.
- **`font_path_fallback()`** — returns path to JetBrains Mono for potential use as a fallback font.

### Changed
- **Viewport height** — reduced from 1080 to 960 for a more compact default window.
- **Chord box dimensions** — narrowed from 154→140 px, height 89→90 px.
- **Chord tab layout** — key/scale/7th toggle moved into a single top row above the two-panel layout.
- **Fretboard centering** — both mini and large fretboards now center horizontally using dynamic string spacing.
- **Voicing label** — padded to constant 8-character width to prevent layout shifts.
- **Volume slider** — changed from float 0.0-1.0 to integer 0-100 with percentage-based internal conversion.
- **Wave type combo** — now displays user-friendly names; toolbar and Sound Settings combos stay in sync.
- **Speaker indicators** — removed blinking speaker dots from both chord list and progression cells. Play bars remain as the sole visual playback indicator.
- **Toolbar layout** — volume label no longer accent-colored, visual separators between control groups.

### Removed
- **Speaker indicator dots** — `spkr_dot_*` and `prog_spkr_dot_*` draw calls removed. `_refresh_speaker_indicators()` simplified to only handle play bars.
- **`on_sound_mode_change` callback** — consolidated into `on_wave_type_change`.

### Fixed
- **Progression fill only filled first row** — `on_prog_fill()` now fills from the selected cell across all 32 cells.
- **Progression piano centered on wrong octave** — `_update_prog_piano()` now dynamically rebuilds the canvas centered on the cell's octave.

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

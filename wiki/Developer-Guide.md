# Developer Guide

Project architecture, build instructions, and contribution guidelines for KLO Chords.

---

## Project Architecture

```
src/klo_chords/
├── __init__.py           Package init + version
├── __main__.py           python -m klo_chords entry point
├── gui.py                UI layout construction + main render loop
├── state.py              Global state, all callbacks, chord/progression management
├── chords.py             Music theory engine (scales, chords, voicings)
├── chord_shapes.py       Guitar shape loading, validation, de-duplication, ranking
├── chord_suggestions.py  Smart suggestion engine (diatonic, borrowed, secondary dom.)
├── chord_box.py          Chord name tile and progression grid cell rendering
├── undo_manager.py       Command-pattern undo/redo with batch support
├── theme.py              Color palette, font/icon asset path resolution
├── quality.py            Chord quality symbol and spelled-name formatting
├── fretboard.py          Mini and large fretboard rendering
├── piano.py              Single-octave and multi-octave piano keyboard rendering
├── sound.py              Streaming audio engine (sounddevice + numpy)
├── dpg_keyboard.py       Cross-platform modifier key (Ctrl/Cmd/Shift) polling
└── assets/
    ├── chords/guitar_standard.json    Curated guitar chord shapes
    ├── fonts/verdana.ttf              Primary font
    ├── fonts/JetBrainsMono-Regular.ttf Fallback font
    └── icons/app_icon.ico            Application icon
```

## Technology Stack

| Component | Technology |
|---|---|
| GUI Framework | [Dear PyGui](https://github.com/hoffstadt/DearPyGui) |
| Audio Engine | [sounddevice](https://python-sounddevice.readthedocs.io/) + [numpy](https://numpy.org/) |
| Packaging | setuptools + pyproject.toml |
| CI/CD | GitHub Actions |

## Key Design Patterns

### State Management (`state.py`)

All application state is global module-level in `state.py`. Callbacks are defined here and imported by `gui.py`. The progression grid uses `ProgCell` dataclasses from `chords.py`.

### Undo/Redo (`undo_manager.py`)

Uses the Command pattern:
- Each operation stores `do_fn` and `undo_fn` callables
- Batch operations group multiple commands into a single undo step
- Singleton `UndoManager` instance accessed via `get_undo_manager()`

### Chord Suggestions (`chord_suggestions.py`)

- Analyzes neighboring cells for context
- Generates categorized `Suggestion` objects
- Ranks by voice-leading cost to neighbors
- Supports hidden categories (advanced chords)

### Keyboard Module (`dpg_keyboard.py`)

- Polls Ctrl/Shift state every frame via `dpg.is_key_down()`
- macOS Cmd key tracked via DPG key press/release handlers (codes 527/663)
- `toggle_is_down()` returns platform-native modifier: Cmd on macOS, Ctrl on Windows/Linux

### Sound Engine (`sound.py`)

- Continuous streaming callback (never stops)
- Numpy-vectorized voice bank with per-voice phase, amplitude, age, and release state
- Voice leading with anti-drift and equal-loudness compensation
- Mute/unmute preserves volume setting

## Development Setup

```bash
# Clone
git clone <repo-url>
cd KLO_Chords

# Create conda environment
conda env create -f environment.yml
conda activate klo_music

# Install in editable mode
pip install -e .

# Run
python -m klo_chords
```

### Running Tests

```bash
python -m pytest tests/
```

## Build & Release

### CI Pipeline (`.github/workflows/build.yml`)

- Triggers on every push to any branch
- Builds for macOS and Windows
- macOS: PyInstaller `.app` bundle
- Windows: PyInstaller single-file `.exe`
- Branch name sanitized into artifact filename suffix

### PyInstaller Build Notes

- `--collect-all dearpygui` required for Dear PyGui's native extensions
- Font and chord data bundled via `--add-data` flags
- macOS requires `pyobjc-framework-Cocoa` and `pillow` for icon conversion

## Dependencies

```text
dearpygui     # GUI framework
sounddevice   # Audio playback
numpy         # Vectorized audio generation
```

## Contributing

1. Create a feature branch from `main`
2. Make changes following existing code conventions
3. Update `CHANGELOG.md` with your changes
4. Run tests: `python -m pytest tests/`
5. Submit a pull request

### Code Style

- Follow PEP 8
- Module-level globals for state
- Use dataclasses for structured data
- Callbacks in `state.py`, layout in `gui.py`
- New modules should have clear docstrings

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for the complete version history.

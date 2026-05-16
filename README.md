# KLO Chords

A music theory desktop app built with [Dear PyGui](https://github.com/hoffstadt/DearPyGui). Explore diatonic chords for any key and scale, build chord progressions, visualize guitar fretboards and piano keyboards, play back with a streaming audio engine, and connect MIDI devices — all in one window.

## Features

### Chords Tab
- **Key & Scale selector** — 12 keys × 12 scale types (Major, Natural/Harmonic/Melodic minor, Pentatonic Major/Minor, Blues, Dorian, Phrygian, Lydian, Mixolydian, Locrian). Key dropdowns use conventional accidentals (Bb, not A#).
- **Diatonic chord list** — Roman numeral, chord name, and mini fretboard for each scale degree. Press `1`–`7` to select and play.
- **Chord detail panel** — full name, sounding notes, large interactive fretboard, multiple voicings (Prev/Next), fret-number or note-name display.
- **Piano keyboard** — chord notes in gold, scale notes in blue, bass note in green.

### Progression Tab
- **8×4 grid** (32 cells) — click any cell to set root, quality, and inversion. Roman numeral computed per-cell against the current key/scale.
- **Keyboard shortcuts** — `1–8`, `Q–I`, `A–K`, `Z–,` map to all 32 cells. `Shift+←/→` steps the selected cell's root note by semitone.
- **Arrow key editing** — `←/→` cycles inversion, `↑/↓` cycles quality.
- **Multi-select** — `Shift+Click` range select, `Ctrl/Cmd+Click` toggle, `Ctrl/Cmd+Shift+Click` additive range. Copy/Paste with Replace, Insert, Swap modes and Linear / Preserve-Shape layout options.
- **Undo/Redo** — `Ctrl+Z` / `Ctrl+Y` with 100-step command-pattern history and batch grouping.
- **Chord suggestions** — color-categorized suggestions (Safe, Borrowed, Secondary Dominant, Chromatic Mediant, Advanced) for any selected cell. Category navigation with ◀/▶. Multi-select and copy with voice-leading optimization.
- **Progression Import/Export** — save and restore the full grid as a `.kloc` file via native OS file dialogs.

### MIDI Tab
- **Port management** — auto-detected input/output ports with channel selectors and Connect buttons.
- **Virtual MIDI output** — creates a `KLO_Chords` virtual port visible to DAWs and other software. Toggled from Settings; state persists across launches.
- **Real-time chord output** — chord plays and note toggles send MIDI note-on/off to the connected device. Legato mode holds shared notes between chords.
- **Program Change** — GM / Roland / Yamaha modes with bank select MSB/LSB fields, Prev/Next controls, and Send button.
- **Sync / Transport** — MIDI clock send (Start, Continue, Stop buttons), BPM display with smoothing, song position tracking, 24 ppqn clock count.
- **Piano visualizer** — 7-key velocity-mapped display lights up on incoming MIDI notes.
- **CC Monitor** — dynamic progress bars for any received control change message.
- **MIDI log** — filterable, timestamped log of all sent/received messages with optional hex display toggle.

### Audio Engine
- **Streaming engine** — `sounddevice` + numpy, no file I/O. Single continuous `OutputStream` — voices added/released dynamically for click-free playback.
- **Waveforms** — triangle, sine, sawtooth with polyBLEP anti-aliasing in Smooth and Responsive modes.
- **Playback modes** — Toggle (latch on/off, same chord toggles) or One-Shot (~0.8 s auto-release tail).
- **Legato** — shared notes between chords held smoothly instead of re-struck.
- **Sub oscillator** — adds a deep bass note one octave below the chord root for fuller sound.
- **Velocity** — per-note random velocity with configurable range and center.
- **Audio quality presets** — Smooth (polyBLEP + tanh soft clipper, 1024-block), Responsive (polyBLEP, 512-block), Legacy (basic, 512-block).
- **Device selection** — choose any output audio device or use System Default.
- **Controls** — volume slider (0–100%), base octave (2–6), mute (`ESC`), stop (`Spacebar`).

### Settings Tab
- All audio parameters persisted to JSON on platform-native paths.
- Jazz chord symbols toggle (Δ, ø, − glyphs instead of plain text).
- Show/hide keyboard shortcut labels on chord tiles and grid cells.
- Virtual MIDI output enable/disable.
- Reset button restores all settings to factory defaults.

## Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| `Spacebar` | Stop current sound |
| `ESC` | Toggle mute |
| `Cmd/Ctrl+1–4` | Switch tabs (Chords / Progression / MIDI / Settings) |
| `Ctrl+Z` / `Ctrl+Y` | Undo / Redo (progression grid) |

**Chord tab:** `1`–`7` select and play diatonic chords.

**Progression tab:**

| Row | Keys |
|---|---|
| Row 0 | `1`–`8` |
| Row 1 | `Q`–`I` |
| Row 2 | `A`–`K` |
| Row 3 | `Z`–`,` |

`Ctrl` + cell key = select without playing. `Shift` + cell key = toggle-select cell. `Shift+←/→` = step root note. `←/→` = cycle inversion. `↑/↓` = cycle quality. `Ctrl+↑/↓` = move row. `Delete` = clear selected.

**Suggestion panel** (visible when a progression cell is selected):

| Shortcut | Action |
|---|---|
| `Alt/Opt + 1` | Play / toggle off the original (current) cell card |
| `Alt/Opt + 2–9` | Play / toggle off a suggestion card |
| `Shift + Alt/Opt + 1` | Range-select the original card |
| `Shift + Alt/Opt + 2–9` | Range-select from anchor to card |
| `Cmd/Ctrl + Alt/Opt + 1` | Toggle-select original card |
| `Cmd/Ctrl + Alt/Opt + 2–9` | Toggle-select individual card |
| `Shift+Click` | Range-select cards |
| `Cmd/Ctrl+Click` | Toggle-select card |
| `Ctrl/Cmd+C` | Copy selected cards with voice-leading |

## Quick Start

**macOS / Linux:**
```bash
./run.sh
```

**Windows:**
```batch
run.bat
```

The launcher creates the Conda environment (if needed), installs dependencies, and starts the app.

**Manual:**
```bash
conda env create -f environment.yml
conda activate klo_music
pip install -e .
python -m klo_chords
```

**Run tests:**
```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## Project Structure

```text
KLO_Chords/
├── pyproject.toml          Package config, pytest & coverage settings
├── environment.yml         Conda environment definition
├── requirements.txt        Runtime dependencies (flat list)
├── run.bat / run.sh        Launcher scripts (auto-setup + launch)
├── CHANGELOG.md            Release history
│
├── src/klo_chords/
│   ├── __init__.py         Package version
│   ├── __main__.py         Entry: python -m klo_chords
│   ├── state.py            Global state + all DPG callbacks
│   │
│   ├── core/               Music theory & persistence (no GUI deps)
│   │   ├── chords.py           Notes, scales, diatonic chords
│   │   ├── chord_shapes.py     Guitar shape loading & ranking
│   │   ├── chord_suggestions.py  Suggestion engine
│   │   ├── quality.py          Chord quality formatting
│   │   ├── constants.py        Grid dimensions (8×4)
│   │   ├── prefs.py            JSON preference persistence
│   │   └── undo_manager.py     Command-pattern undo/redo
│   │
│   ├── audio/              Sound & MIDI
│   │   ├── sound.py            Streaming audio engine
│   │   └── midi_engine.py      MIDI driver, ports, sync, log
│   │
│   ├── gui/
│   │   └── app.py              DPG window layout + event loop
│   │
│   ├── rendering/          Custom drawlist rendering
│   │   ├── fretboard.py        Mini & large guitar diagrams
│   │   ├── piano.py            Single & multi-octave keyboards
│   │   ├── chord_box.py        Chord tiles & grid cells
│   │   └── theme.py            Colors, fonts, asset paths
│   │
│   ├── widgets/
│   │   └── dpg_keyboard.py     Modifier key polling
│   │
│   ├── helpers/
│   │   └── console_logging.py  MIDI note/event formatting
│   │
│   └── assets/
│       ├── chords/guitar_standard.json
│       ├── fonts/ (DejaVuSans, JetBrainsMono, verdana, NotoSans)
│       └── icons/app_icon.ico
│
├── tests/
│   ├── conftest.py             Shared fixtures
│   ├── test_chords.py          Note/pc, scales, diatonic chords
│   ├── test_chord_shapes.py    Shape loading & validation
│   ├── test_chord_suggestions.py  Suggestion engine
│   ├── test_console_logging.py
│   ├── test_prefs.py           Persistence round-trips
│   ├── test_quality.py         Quality formatting
│   └── test_undo_manager.py    Do/undo/redo command pattern
│
├── .github/workflows/
│   └── build.yml               CI: test + PyInstaller (macOS/Windows)
│
└── utils/
    └── test_keys.py             DPG key code diagnostic tool
```

## Guitar Shape Pipeline

Shapes are in low-to-high string order: `E A D G B e`. The system uses three tiers:
1. **Curated library** — `guitar_standard.json` contains hand-entered canonical shapes.
2. **CAGED barre generation** — barre chord forms derived from open positions.
3. **Brute-force search** — generic shape search across frets 0–9.

At runtime, shapes are validated against the chord's pitch classes (non-chord tones rejected), de-duplicated, and ranked by playability score (lower = better) using a penalty system that rewards open strings, root bass notes, and compact spans.

## Dependencies

- Python 3.11+
- [Dear PyGui](https://github.com/hoffstadt/DearPyGui) — GUI framework
- sounddevice — Real-time audio output
- numpy — Vectorized audio synthesis
- python-rtmidi — MIDI I/O
- pytest, pytest-cov (dev) — Testing

## License

MIT

---

*For detailed developer documentation and a user guide, see the [KLO Chords Wiki](https://github.com/your-org/KLO_Chords.wiki).*

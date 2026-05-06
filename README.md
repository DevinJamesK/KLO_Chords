# KLO Chords

A music theory desktop app built with [Dear PyGui](https://github.com/hoffstadt/DearPyGui) that shows diatonic chords for any key and scale, with guitar fretboard diagrams, a piano keyboard visualizer, and a streaming audio engine.

## Features

- **Key & Scale selector** — Pick any key (C, C#, D, ...) and scale type (Major, Natural Minor, Harmonic Minor, Melodic Minor, Pentatonic, Blues, Dorian, Phrygian, ...)
- **Diatonic chord list** — Shows chords built from the selected scale, each with:
  - Roman numeral degree (dynamically computed from the chord's actual root vs the key/scale)
  - Chord name and notes in a bordered tile
  - A mini fretboard preview
  - Play bar indicator when sounding
- **Chord detail panel** — Click any chord to see:
  - Full name with spelled-out quality
  - Chord notes and intervals
  - Large interactive fretboard diagram
  - Multiple voicings (navigate with Prev/Next)
  - Fretboard display modes: fret numbers or note names
- **Streaming audio engine** — Chords play automatically on selection via `sounddevice` + numpy. Waveforms: triangle (default), sine, sawtooth.
- **Playback modes** — Toggle (on/off per chord) or One-Shot (~1s burst).
- **Legato mode** — Notes shared between consecutive chords are held smoothly.
- **Velocity controls** — Random velocity per note with configurable min/max range.
- **Base octave slider** — Shift chord voicings up or down.
- **Piano keyboard** — Highlights chord notes (gold), scale notes (blue), and bass note (green).
- **Inversion display** — Shows the current inversion name and sounding notes below the keyboard.
- **Number key shortcuts (1-7)** — Press 1-7 to select and play diatonic chords.
- **Mute/Unmute** — Press `ESC` to toggle mute; `Spacebar` to stop playback.
- **Validated guitar voicings** — Loads local guitar chord data, rejects shapes with wrong notes, de-duplicates results, and ranks shapes by playability.
- **Fretboard note-name mode** — Toggle between fret numbers and actual note names on fretboard dots.
- **Progression grid** — 7-column × 4-row grid for building chord progressions. Click any cell to edit root, quality, and inversion. Each cell shows the chord name, notes, and a roman numeral dynamically computed against the current key/scale.
- **Multi-select in progression** — Shift+click to select a range of cells, Ctrl/Cmd+click to toggle individual cell selection. Copy (Ctrl+C) and Paste (Ctrl+V) with multiple paste modes:
  - **Replace mode** — overwrites cells starting at the paste position
  - **Insert mode** — shifts existing cells right to make room
  - **Swap mode** — exchanges clipboard contents with target cells
  - **Preserve Shape paste** — keeps the original 2D row/column layout
- **Undo/Redo** — Full command-pattern undo/redo (Ctrl+Z / Ctrl+Y) for all progression grid operations.
- **Delete selected cells** — Press Delete to clear all multi-selected cells at once.
- **Move selection** — Ctrl+Up / Ctrl+Down moves selected cells one row up or down.
- **Chord suggestions** — Select any cell (empty or non-empty) to see categorized chord suggestions: safe (diatonic), borrowed, secondary dominants, chromatic mediants, and advanced chords. Click a suggestion to instantly apply it to the cell.
- **Clear All** — Red "Clear All" button resets all progression grid cells, with automatic sound stop.

## Quick Start

### Option 1: Launcher Scripts (Recommended)

**macOS / Linux:**
```bash
./run.sh
```

**Windows:**
```batch
run.bat
```

The launcher automatically creates the Conda environment (if needed), installs dependencies, and starts the app.

### Option 2: Manual Setup

```bash
# Create Conda environment
conda env create -f environment.yml
conda activate klo_music

# Or use pip + venv
pip install -e .

# Run
python -m klo_chords
```

## Keyboard Shortcuts

### Global

| Shortcut | Action |
|---|---|
| `Spacebar` | Stop current sound |
| `ESC` | Toggle mute on/off |
| `Ctrl+Z` | Undo (progression grid) |
| `Ctrl+Y` | Redo (progression grid) |

### Chord Tab (Diatonic Chords)

| Shortcut | Action |
|---|---|
| `1` – `7` | Select & play diatonic chord |
| Same key again | Toggle off playing chord |

### Progression Tab

#### Cell Selection & Playback

| Shortcut | Action |
|---|---|
| `1` – `7` | Select & play cells in row 0 |
| `Q` – `U` | Select & play cells in row 1 |
| `A` – `J` | Select & play cells in row 2 |
| `Z` – `M` | Select & play cells in row 3 |
| `Ctrl` + any above | Select cell without playing sound |

#### Cell Editing

| Shortcut | Action |
|---|---|
| `←` / `→` | Cycle inversion of selected cell |
| `↑` / `↓` | Cycle quality of selected cell |
| `Ctrl+↑` / `Ctrl+↓` | Move selection up/down one row |

#### Multi-Select & Clipboard

| Shortcut | Action |
|---|---|
| `Shift+Click` | Range-select cells |
| `Ctrl/Cmd+Click` | Toggle individual cell selection |
| `Ctrl+C` | Copy selected cells |
| `Ctrl+V` | Paste cells |
| `Delete` | Clear selected cells |

## Controls

| Control | Action |
|---|---|
| Key dropdown | Change root key |
| Scale dropdown | Change scale type |
| Include 7th chords | Toggle triads vs. seventh chords |
| Click a chord box | Select and view details |
| < Prev / Next > | Cycle through fretboard voicings |
| 1-7 keys | Select and play diatonic chords |
| Volume slider | Adjust master volume |
| Wave combo | Switch waveform (triangle/sine/sawtooth) |
| Legato toggle | Enable smooth note transitions |
| Sound tab | Full audio configuration panel |
| Show Note Names | Toggle fretboard display mode |
| Fill Chords | Fill progression grid with diatonic chords |
| Clear All | Reset all progression cells |
| Show Suggestions | Open chord suggestion panel |
| Paste Mode | Choose insert/replace/swap for paste |
| Paste Shape | Choose linear or preserve-shape paste |

## Chord Shape Data

Guitar shapes are stored in normal low-to-high string order: `E A D G B e`.

Example:

```text
x32010 = muted low E, A3, D2, G0, B1, high e0
```

The app uses `chord_shapes.py` to:

- load local JSON chord-shape data
- validate each shape against the chord's pitch classes
- reject shapes that contain non-chord tones
- de-duplicate matching fret patterns
- rank shapes by natural playability
- fall back to generated CAGED/search shapes when no curated shape exists

The bundled data starts with hand-curated canonical shapes and source labels for future cross-checking against MIT-licensed chord datasets such as:

- [tombatossals/chords-db](https://github.com/tombatossals/chords-db)
- [szaza/guitar-chords-db-json](https://github.com/szaza/guitar-chords-db-json)

## Project Structure

```text
src/klo_chords/
|-- __init__.py                 Package init
|-- __main__.py                 python -m entry point
|-- gui.py                      UI layout + main loop
|-- state.py                    Global state and callbacks
|-- chords.py                   Music theory engine
|-- chord_shapes.py             Guitar shape loading, validation, and ranking
|-- chord_suggestions.py        Smart chord suggestion engine
|-- undo_manager.py             Undo/redo command-pattern manager
|-- theme.py                    Colors, font path, and icon path
|-- quality.py                  Chord quality formatting
|-- chord_box.py                Chord name tile and progression cell rendering
|-- fretboard.py                Mini and large fretboard drawing
|-- piano.py                    Piano keyboard rendering
|-- sound.py                    Streaming audio engine (sounddevice + numpy)
|-- dpg_keyboard.py             Cross-platform modifier key polling
`-- assets/
    |-- chords/guitar_standard.json
    |-- fonts/verdana.ttf
    `-- icons/app_icon.ico
```

## Download

Pre-built binaries are produced automatically by GitHub Actions on every push to `main`.

- **Windows** — `KLO Chords.exe` (single-file executable)
- **macOS** — `KLO Chords.app` bundle

Download the latest build from the [Actions](../../actions) tab.

## Dependencies

- Python 3.11+
- [Dear PyGui](https://github.com/hoffstadt/DearPyGui) >= 1.10

## License

MIT

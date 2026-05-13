# KLO Chords

A music theory desktop app built with [Dear PyGui](https://github.com/hoffstadt/DearPyGui). Shows diatonic chords for any key and scale, with guitar fretboard diagrams, a piano keyboard, a streaming audio engine, and MIDI output.

## Features

### Chord Tab
- **Key & Scale selector** — `C Db D Eb E F F# G Ab A Bb B` × Major, Minor, Modal, Pentatonic, Blues, and more. Key dropdowns use conventional accidentals (Bb, not A#).
- **Diatonic chord list** — Roman numeral, chord name, and mini fretboard for each scale degree. Press `1`–`7` to select and play.
- **Chord detail panel** — full name, sounding notes, large interactive fretboard, multiple voicings (Prev/Next), fret-number or note-name display.
- **Piano keyboard** — chord notes in gold, scale notes in blue, bass note in green.

### Progression Tab
- **8×4 grid** — click any cell to set root, quality, and inversion. Roman numeral computed per-cell against the current key/scale.
- **Keyboard shortcuts** — `1–8`, `Q–I`, `A–K`, `Z–,` map to all 32 cells. `Shift+←/→` steps the selected cell's root note by semitone using the key's accidental spelling.
- **Arrow key editing** — `←/→` cycles inversion, `↑/↓` cycles quality.
- **Multi-select** — `Shift+Click` range select, `Ctrl/Cmd+Click` toggle. Copy/Paste with Replace, Insert, Swap, and Preserve-Shape modes.
- **Undo/Redo** — `Ctrl+Z` / `Ctrl+Y`, full history.
- **Chord suggestions** — categorized suggestions (diatonic, borrowed, secondary dominants, chromatic mediants) for any selected cell. Shift+click for range select, Cmd/Ctrl+click to toggle individual cards. `Ctrl/Cmd+C` copies selected suggestion cards with voice-leading data.
- **Progression Import/Export** — save and restore the full grid as a `.kloc` file via native OS file dialogs.

### MIDI Tab
- **MIDI output** — chord plays and note toggles send real-time MIDI note-on/off to the selected device and channel.
- **Input/Output port selectors** — auto-detected; each on one row with channel selector and Connect button.
- **Program Change** — mode combo (Program / Bank-Select), optional Bank MSB/LSB fields, Prev/Program/Next controls, Send button.
- **MIDI log** — timestamped log of all sent/received messages with hex display toggle.
- **Sync with audio** — MIDI note-offs fire on spacebar, tab switch, transport stop, and app close.

### Audio
- **Streaming audio engine** — `sounddevice` + numpy, no file I/O. Waveforms: triangle, sine, sawtooth.
- **Playback modes** — Toggle (on/off) or One-Shot (~1 s burst). Legato holds shared notes between chords.
- **Audio quality presets** — Smooth (polyBLEP + soft clipper), Responsive, Legacy.
- **Controls** — volume slider, base octave, velocity range, mute (`ESC`), stop (`Spacebar`).

### Settings Tab
- Persistent preferences (wave, octave, velocity, keybind display, fretboard mode).
- Reset button clears saved preferences and resets all controls to defaults.

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
conda env create -f environment.yml && conda activate klo_music
# or: pip install -e .
python -m klo_chords
```

## Project Structure

```text
src/klo_chords/
├── gui.py                  UI layout + main loop
├── state.py                Global state and callbacks
├── chords.py               Music theory engine
├── sound.py                Streaming audio engine
├── midi_tab.py             MIDI tab UI, port management, output driver
├── prefs.py                Persistent preferences (JSON, platform paths)
├── chord_shapes.py         Guitar shape loading, validation, ranking
├── chord_suggestions.py    Chord suggestion engine
├── undo_manager.py         Undo/redo command-pattern manager
├── theme.py                Colors and font paths
├── quality.py              Chord quality formatting
├── chord_box.py            Chord tile and progression cell rendering
├── fretboard.py            Mini and large fretboard drawing
├── piano.py                Piano keyboard rendering
├── dpg_keyboard.py         Cross-platform modifier key polling
└── assets/
    ├── chords/guitar_standard.json
    ├── fonts/verdana.ttf
    ├── fonts/NotoSans-Regular.ttf
    └── icons/app_icon.ico
```

## Guitar Shape Data

Shapes are in low-to-high string order: `E A D G B e`. The bundled `guitar_standard.json` contains hand-curated canonical shapes. At runtime, `chord_shapes.py` validates each shape against the chord's pitch classes, rejects non-chord tones, de-duplicates, and ranks by playability.

## Dependencies

- Python 3.11+
- [Dear PyGui](https://github.com/hoffstadt/DearPyGui), sounddevice, numpy, python-rtmidi

## License

MIT

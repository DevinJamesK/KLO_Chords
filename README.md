# KLO Chords

A music theory desktop app built with [Dear PyGui](https://github.com/hoffstadt/DearPyGui) that shows diatonic chords for any key and scale, with guitar fretboard diagrams and a piano keyboard visualizer.

## Features

- **Key & Scale selector** - Pick any key (C, C#, D, ...) and scale type (Major, Natural Minor, Harmonic Minor, Melodic Minor, Pentatonic, Blues, Dorian, Phrygian, ...)
- **Diatonic chord list** - Shows chords built from the selected scale, each with:
  - Roman numeral degree in its own fixed column (left-aligned, `I`–`vii°`)
  - Chord name and notes in a bordered tile
  - A mini fretboard preview
- **Chord detail panel** - Click any chord to see:
  - Full name with spelled-out quality
  - Chord notes and intervals
  - Large interactive fretboard diagram
  - Multiple voicings (navigate with Prev/Next)
- **Validated guitar voicings** - Loads local guitar chord data, rejects shapes with wrong notes, de-duplicates results, and ranks shapes by playability.
- **Piano keyboard** - Highlights scale notes (blue) and chord notes (yellow)

## Usage

### Conda / Miniforge Setup

```powershell
conda env create -f environment.yml
conda activate klo_music
```

### Run

```bash
python -m klo_chords
```

Or directly:

```bash
python src/klo_chords/gui.py
```

### Controls

| Control | Action |
|---|---|
| Key dropdown | Change root key |
| Scale dropdown | Change scale type |
| Include 7th chords | Toggle triads vs. seventh chords |
| Click a chord box | Select and view details |
| < Prev / Next > | Cycle through fretboard voicings |

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
|-- theme.py                    Colors, font path, and icon path
|-- quality.py                  Chord quality formatting
|-- chord_box.py                Chord name tile rendering
|-- fretboard.py                Mini and large fretboard drawing
|-- piano.py                    Piano keyboard rendering
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

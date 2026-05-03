# KLO Chord Sample

A music theory desktop app built with [Dear PyGui](https://github.com/hoffstadt/DearPyGui) that shows diatonic chords for any key and scale, with guitar fretboard diagrams and a piano keyboard visualizer.

## Features

- **Key & Scale selector** — Pick any key (C, C#, D, ...) and scale type (Major, Natural Minor, Harmonic Minor, Melodic Minor, Pentatonic, Blues, Dorian, Phrygian, ...)
- **Diatonic chord list** — Shows the 7 chords built from the selected scale, each with:
  - Roman numeral degree + chord name (e.g. `I  C`, `ii  Dmin`, `V7  G7`)
  - Notes in the chord
  - A mini fretboard preview
- **Chord detail panel** — Click any chord to see:
  - Full name with spelled-out quality
  - Chord notes and intervals
  - Large interactive fretboard diagram
  - Multiple voicings (navigate with Prev/Next)
- **Piano keyboard** — Highlights scale notes (blue) and chord notes (yellow)

## Usage

### Run

```bash
python -m klo_chord_sample
```

Or directly:

```bash
python src/klo_chord_sample/gui.py
```

### Controls

| Control | Action |
|---|---|
| Key dropdown | Change root key |
| Scale dropdown | Change scale type |
| Include 7th chords | Toggle triads vs. seventh chords |
| Click a chord box | Select and view details |
| < Prev / Next > | Cycle through fretboard voicings |

## Project Structure

```
src/klo_chord_sample/
├── __init__.py      Package init
├── __main__.py      `python -m` entry point
├── gui.py           UI layout + main loop
├── state.py         Global state and callbacks
├── chords.py        Music theory engine (scales, chords, diagrams)
├── theme.py         Colors and font path
├── quality.py       Chord quality formatting
├── chord_box.py     Chord name tile rendering
├── fretboard.py     Mini and large fretboard drawing
├── piano.py         Piano keyboard rendering
└── assets/fonts/    JetBrainsMono font
```

## Dependencies

- Python 3.10+
- [Dear PyGui](https://github.com/hoffstadt/DearPyGui) >= 1.10

## License

MIT

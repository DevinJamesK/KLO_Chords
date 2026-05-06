# KLO Chords Wiki

Welcome to the KLO Chords wiki! KLO Chords is a music theory desktop application built with [Dear PyGui](https://github.com/hoffstadt/DearPyGui) that helps you explore diatonic chords, build chord progressions, and visualize guitar fretboards — all with a real-time streaming audio engine.

## Quick Navigation

- **[Keyboard Shortcuts](Keyboard-Shortcuts)** — Complete reference of every keyboard shortcut, organized by context
- **[Features Guide](Features-Guide)** — In-depth walkthrough of all features: chord theory, progression grid, chord suggestions, sound engine
- **[Developer Guide](Developer-Guide)** — Project architecture, build instructions, and contribution guidelines

## Installation

### Quick Launch

```bash
# macOS / Linux
./run.sh

# Windows
run.bat
```

### Manual Setup

```bash
conda env create -f environment.yml
conda activate klo_music
pip install -e .
python -m klo_chords
```

## Core Concepts

### Tabs

The app has three main tabs:

1. **Chords** — Explore diatonic chords for any key/scale combination with piano keyboard and guitar fretboard visualizations
2. **Progression** — Build custom chord progressions in a 7×4 grid with multi-select, copy/paste, and smart chord suggestions
3. **Sound** — Configure the audio engine: waveform, velocity, playback mode, base octave

### Always-Visible Toolbar

The toolbar at the top is persistent across all tabs:

- **Volume** — 0–100% master volume slider
- **Legato** — Smooth note transitions between consecutive chords
- **Wave** — Triangle / Sine / Sawtooth waveform selector with live preview

## Keyboard Shortcuts at a Glance

| Context | Most Important Shortcuts |
|---|---|
| Global | `Spacebar` stop, `ESC` mute, `Ctrl+Z` undo, `Ctrl+Y` redo |
| Chord Tab | `1`–`7` play diatonic chords |
| Progression Tab | `1`–`7`/`Q`–`U`/`A`–`J`/`Z`–`M` play cells; `←` `→` `↑` `↓` edit |
| Multi-Select | `Shift+Click` range, `Ctrl/Cmd+Click` toggle, `Ctrl+C/V` copy/paste |

See the complete **[Keyboard Shortcuts](Keyboard-Shortcuts)** page for every shortcut.

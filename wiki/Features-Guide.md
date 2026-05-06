# Features Guide

In-depth walkthrough of all major features in KLO Chords.

---

## 1. Chord Tab — Diatonic Chord Explorer

Select any key and scale to see all diatonic chords.

### Key & Scale Selector

- **Key**: 12 chromatic keys (C, C#, D, ..., B)
- **Scale**: 12 scale types including Major, Natural Minor, Harmonic Minor, Melodic Minor, Pentatonic Major/Minor, Blues, and all seven modes (Dorian, Phrygian, Lydian, Mixolydian, Locrian)
- **Include 7th**: Toggle between triads and seventh chords

### Chord List (Left Panel)

Each chord row shows:
- **Degree column** — Fixed-width roman numeral (I, ii, iii, IV, V, vi, vii°) aligned left
- **Chord name tile** — Root note + quality symbol with border highlighting when selected
- **Mini fretboard** — Compact guitar diagram showing one playable voicing
- **Play bar** — Colored bar at the bottom lights up green when sounding
- **Click to select** — Click any chord row to view full details and trigger playback

### Chord Detail Panel (Right Panel)

When a chord is selected:
- **Degree / Root** — Roman numeral and root note
- **Quality** — Spelled-out quality name (e.g., "minor 7")
- **Notes / Intervals** — Individual note names and semitone intervals
- **Piano Keyboard** — Single-octave keyboard: **Gold** = chord tones, **Blue** = scale-only, **Green** = bass note
- **Inversion Display** — Current inversion name and sounding notes
- **Fretboard** — Large 360×220 diagram with X/O markers, highlighted root, and string names
- **< Prev / Next >** — Cycle through multiple guitar voicings
- **Show Note Names** — Toggle fret numbers vs note names (root in green)

---

## 2. Progression Tab — Chord Progression Builder

Build custom chord progressions in a 7×4 clickable grid.

### Grid Basics

- **7 columns × 4 rows** = 28 cells
- Each cell stores: root, quality, inversion, octave, and voicing index
- Populated cells show: dynamic roman numeral, chord name, and spelled notes

### Cell Detail Panel

Select any cell to edit:
- **Root** — Navigate 12 chromatic roots with < > buttons
- **Quality** — 13 chord qualities: Major, minor, dim, aug, 7, m7, maj7, dim7, m7b5, mmaj7, aug7, sus2, sus4
- **Inversion** — 0 (root), 1 (1st), 2 (2nd), 3 (3rd)
- **Octave** — 0–9 shift
- **Multi-octave piano** — 2-octave keyboard centered on the cell's notes

### Fill & Clear

- **Fill Chords** — Populate all cells with diatonic chords from current key/scale
- **Clear All** — Reset all cells to empty

---

## 3. Chord Suggestions Engine

| Category | Color | Description |
|---|---|---|
| **Safe** | Green | Diatonic chords that fit the key/scale |
| **Borrowed** | Amber | Chords from parallel key (bIII, iv, bVI, bVII) |
| **Secondary Dominant** | Orange | V7 of a diatonic target with resolution labeling |
| **Chromatic Mediant** | Purple | Roots a 3rd from neighboring cells |
| **Advanced** | Gray | Neapolitan, augmented 6th chords |

Suggestions are ranked by voice-leading distance to neighboring cells. Click any suggestion to apply it (undoable).

---

## 4. Multi-Select, Copy/Paste & Undo/Redo

### Selection
- **Click** — Select one cell
- **Shift+Click** — Range-select
- **Ctrl/Cmd+Click** — Toggle individual cell
- Selected cells shown with accent-colored border

### Clipboard
- **Ctrl+C/V** — Copy/paste with Paste Mode (Replace/Insert/Swap) and Paste Shape (Linear/Preserve Shape)
- **Delete** — Clear multi-selected cells

### Undo/Redo
- **Ctrl+Z/Y** — Full undo/redo for all grid operations
- Batch operations grouped into single undo step
- 100-step history

---

## 5. Sound Engine

Real-time audio synthesis using `sounddevice` + numpy.

| Waveform | Character |
|---|---|
| **Triangle** (default) | Smooth, mellow |
| **Sine** | Pure, flute-like |
| **Sawtooth** | Bright, buzzy |

### Playback Modes
- **Toggle/Latch** — Press to start, same chord to stop
- **One-Shot** — ~0.8s burst with release tail

### Legato
Shared notes between chords are held, only differing notes re-trigger.

### Velocity
Random velocity per note (configurable 1–127 range) for natural dynamics.

---

## 6. Guitar Fretboard Diagrams

### Shape Pipeline
1. Load curated shapes from `guitar_standard.json`
2. Validate against chord pitch classes (reject wrong notes)
3. De-duplicate identical patterns
4. Rank by playability (completeness, span, open strings, bass note)
5. Fall back to CAGED barre and search-based shapes

### Display Modes
- **Fret Numbers** — Fret number inside each dot (default)
- **Note Names** — Actual note name, root in green

---

## 7. Piano Keyboards

| Tab | Type | Highlights |
|---|---|---|
| Chord | Single octave (C–B) | Gold (chord), Blue (scale), Green (bass) |
| Progression | Multi-octave | Same colors, dynamically centered on cell octave |
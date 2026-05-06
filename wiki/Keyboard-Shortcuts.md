# Keyboard Shortcuts

Complete reference of every keyboard shortcut in KLO Chords, organized by context.

## Global Shortcuts

These work on all tabs.

| Shortcut | Action | Notes |
|---|---|---|
| `Spacebar` | Stop current sound | Releases all playing notes immediately |
| `ESC` | Toggle mute on/off | Volume slider turns red when muted; sliding volume auto-unmutes |
| `Ctrl+Z` | Undo | Applies to progression grid operations |
| `Ctrl+Y` | Redo | Re-applies the last undone operation |

---

## Chord Tab — Diatonic Chords

Select and play diatonic chords from the left panel.

| Shortcut | Action | Notes |
|---|---|---|
| `1` | Select & play I chord | Tonic |
| `2` | Select & play ii chord | Supertonic |
| `3` | Select & play iii chord | Mediant |
| `4` | Select & play IV chord | Subdominant |
| `5` | Select & play V chord | Dominant |
| `6` | Select & play vi chord | Submediant |
| `7` | Select & play vii° chord | Leading tone |
| Same key again | Toggle off current chord | Only in Toggle/Latch playback mode |

**Playback behavior:**
- In **Toggle mode**: Pressing the same key again stops the chord. Pressing a different key switches.
- In **One-Shot mode**: Each key press plays a ~1 second burst.
- With **Legato** enabled: Notes shared between consecutive chords are held smoothly.

---

## Progression Tab — Cell Selection & Playback

The 7×4 progression grid maps 28 cells to the keyboard. Hold `Ctrl` while pressing a key to select without triggering playback.

### Row 0 (Keys `1`–`7`)

| Key | Cell (row, col) |
|---|---|
| `1` | (0, 0) |
| `2` | (0, 1) |
| `3` | (0, 2) |
| `4` | (0, 3) |
| `5` | (0, 4) |
| `6` | (0, 5) |
| `7` | (0, 6) |

### Row 1 (Keys `Q`–`U`)

| Key | Cell (row, col) |
|---|---|
| `Q` | (1, 0) |
| `W` | (1, 1) |
| `E` | (1, 2) |
| `R` | (1, 3) |
| `T` | (1, 4) |
| `Y` | (1, 5) |
| `U` | (1, 6) |

### Row 2 (Keys `A`–`J`)

| Key | Cell (row, col) |
|---|---|
| `A` | (2, 0) |
| `S` | (2, 1) |
| `D` | (2, 2) |
| `F` | (2, 3) |
| `G` | (2, 4) |
| `H` | (2, 5) |
| `J` | (2, 6) |

### Row 3 (Keys `Z`–`M`)

| Key | Cell (row, col) |
|---|---|
| `Z` | (3, 0) |
| `X` | (3, 1) |
| `C` | (3, 2) |
| `V` | (3, 3) |
| `B` | (3, 4) |
| `N` | (3, 5) |
| `M` | (3, 6) |

---

## Progression Tab — Cell Editing

When a cell is selected, these arrow key shortcuts edit its properties.

| Shortcut | Action | Details |
|---|---|---|
| `←` (Left) | Previous inversion | Cycles: Root → 1st → 2nd → 3rd → Root |
| `→` (Right) | Next inversion | Cycles: Root → 3rd → 2nd → 1st → Root |
| `↑` (Up) | Previous quality | Cycles through all 13 chord qualities |
| `↓` (Down) | Next quality | Cycles through all 13 chord qualities |
| `Ctrl+↑` | Move selection up | Swaps selected cells with the row above |
| `Ctrl+↓` | Move selection down | Swaps selected cells with the row below |

---

## Progression Tab — Multi-Select & Clipboard

| Shortcut | Action | Notes |
|---|---|---|
| `Shift+Click` | Range-select cells | Selects all cells between the clicked cell and the current selection |
| `Ctrl+Click` (or `⌘+Click` on macOS) | Toggle individual cell selection | Adds/removes the clicked cell from the multi-selection |
| `Ctrl+C` | Copy selected cells | Copies all selected cells to the internal clipboard |
| `Ctrl+V` | Paste cells | Pastes clipboard at the currently selected position using current Paste Mode and Paste Shape settings |
| `Delete` | Clear selected cells | Clears all multi-selected cells at once (undoable) |

### Paste Modes

Selected via the "Paste Mode" dropdown in the progression tab:

| Mode | Behavior |
|---|---|
| **Replace** | Overwrites cells starting at the paste position |
| **Insert** | Shifts existing cells right to make room for pasted cells |
| **Swap** | Exchanges the clipboard contents with cells at the paste position |

### Paste Shapes

Selected via the "Paste Shape" dropdown:

| Shape | Behavior |
|---|---|
| **Linear** | Pastes cells in a flat row, one after another |
| **Preserve Shape** | Keeps the original 2D row/column layout of the copied selection |

---

## Sound Settings Tab

No special keyboard shortcuts — configure audio parameters via the UI controls:

- Enable/disable sound
- Wave type (Triangle / Sine / Sawtooth)
- Random velocity toggle + min/max range sliders
- Playback mode (Toggle/Latch vs One-Shot)
- Base octave slider (2–6)

---

## macOS Notes

- Use **⌘ Command** instead of Ctrl for modifier+click operations
- `Ctrl+Click` on macOS is interpreted as a right-click by the OS, so `⌘+Click` is used for toggle selection

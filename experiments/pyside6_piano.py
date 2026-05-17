"""PySide6 Piano Keyboard Widget — 3+ octaves, scrollable, with full DPG feature parity.

Features:
  - Multi-octave support (3+ octaves visible, scrollable via wheel)
  - Color coding: gold (chord notes), blue (scale notes), green (bass note)
  - Black-key variants: dark gold for chord, dark blue for scale, dark green for bass
  - highlight_notes() accepts MIDI note numbers, not just pitch classes
  - set_bass_note() for lowest-sounding-note highlighting
  - clear_all() resets both highlights and scale
  - Octave labels drawn on C keys (C3, C4, C5, ...)
  - Wheel-event scrolling through full MIDI range
  - Click interaction with noteClicked signal (midi, name)
  - Self-contained: ``python experiments/pyside6_piano.py``
"""
from __future__ import annotations
import sys, typing as t
from PySide6.QtCore import Qt, Signal, QRectF, QSize, QTimer
from PySide6.QtGui import *
from PySide6.QtWidgets import *

# ── Note names ─────────────────────────────────────────────────────────────────
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

# ── Key geometry (matches DPG constants) ──────────────────────────────────────
_WW, _WH = 48.0, 160.0          # white key width / height
_BW, _BH = 30.0, 100.0          # black key width / height
_WPC = {0, 2, 4, 5, 7, 9, 11}  # white-key pitch classes
_BPC = {1, 3, 6, 8, 10}        # black-key pitch classes
_BXO = [                        # black-key x‑offsets within an octave
    _WW - _BW / 2,
    2 * _WW - _BW / 2,
    4 * _WW - _BW / 2,
    5 * _WW - _BW / 2,
    6 * _WW - _BW / 2,
]
_TH = _WH + 4                   # total canvas height

# Full MIDI range for an 88‑key piano (A0=21 … C8=108)
_MIDI_LO, _MIDI_HI = 21, 108

# ── Colours (RGBA, matches DPG) ────────────────────────────────────────────────
_CW   = QColor(255, 255, 255)    # white key default
_CB   = QColor(24,  24,  28)     # black key default
_CBD  = QColor(40,  40,  50)     # white key border
_CHC  = QColor(255, 210, 50)     # chord highlight – gold (white keys)
_CHCB = QColor(200, 160, 30)     # chord highlight – dark gold (black keys)
_CHS  = QColor(100, 180, 255)    # scale highlight – blue (white keys)
_CHSB = QColor(40,  80,  180)    # scale highlight – dark blue (black keys)
_CHB  = QColor(80,  230, 80)     # bass highlight – green (white keys)
_CHBB = QColor(40,  180, 40)     # bass highlight – dark green (black keys)
_CT   = QColor(20,  20,  30)     # text / accent
_CBG  = QColor(26,  26,  46)     # black key border when highlighted


class PianoWidget(QWidget):
    """A scrollable multi-octave piano keyboard with note highlighting.

    Signals
    -------
    noteClicked(int, str)
        Emitted when a key is clicked.  *int* = MIDI note number,
        *str*  = human‑readable name (e.g. ``"C4"``).
    """

    noteClicked = Signal(int, str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.setMinimumSize(340, 200)       # room for octave labels
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)  # receive wheel events

        # ── State ──────────────────────────────────────────────────────────
        self._hl: dict[int, QColor] = {}    # midi → highlight colour (chord notes)
        self._sp: set[int] = set()          # pitch classes for scale notes
        self._bass_midi: int = -1           # lowest sounding note (‑1 = none)

        # Build lookup lists for the entire 88‑key range
        self._white_midis = [m for m in range(_MIDI_LO, _MIDI_HI + 1) if m % 12 in _WPC]
        self._black_midis = [m for m in range(_MIDI_LO, _MIDI_HI + 1) if m % 12 in _BPC]

        # The white key that will be centred in the viewport
        self._scroll_midi: int = 60         # C4

    # ── Public API ─────────────────────────────────────────────────────────

    def highlight_note(self, midi: int, color: QColor | None = None) -> None:
        """Highlight a single MIDI note."""
        if color is None:
            color = _CHC
        self._hl[midi] = color
        self.update()

    def highlight_notes(self, midis: t.Iterable[int], color: QColor | None = None) -> None:
        """Highlight multiple MIDI notes (chord tones)."""
        if color is None:
            color = _CHC
        for m in midis:
            self._hl[m] = color
        self.update()

    def set_scale_pcs(self, midis: t.Iterable[int]) -> None:
        """Set scale notes (displayed in blue unless overridden by chord/bass).

        Accepts a list of MIDI note numbers; pitch classes are extracted
        internally.
        """
        self._sp = {m % 12 for m in midis}
        self.update()

    def set_bass_note(self, midi: int) -> None:
        """Set the lowest sounding note (highlighted in green).

        The bass note is only highlighted when it is also a chord note.
        Pass -1 to clear.
        """
        self._bass_midi = midi
        self.update()

    def clear_highlights(self) -> None:
        """Clear chord‑note highlights only (keeps scale)."""
        self._hl.clear()
        self.update()

    def clear_all(self) -> None:
        """Clear both chord highlights and scale notes, and reset bass."""
        self._hl.clear()
        self._sp.clear()
        self._bass_midi = -1
        self.update()

    # ── Sizing ─────────────────────────────────────────────────────────────

    def sizeHint(self) -> QSize:
        return QSize(52 * 48 + 4, 200)

    def minimumSizeHint(self) -> QSize:
        return QSize(340, 200)

    # ── Scrolling ──────────────────────────────────────────────────────────

    def _visible_range(self) -> tuple[int, int]:
        """Return *(first_idx, last_idx)* into ``_white_midis`` for the visible keys."""
        w = self.width()
        n = max(7, int(w // _WW))          # number of white keys that fit
        try:
            ci = self._white_midis.index(self._scroll_midi)
        except ValueError:
            ci = 0
        fi = ci - n // 2
        li = fi + n
        total = len(self._white_midis)
        if fi < 0:
            fi, li = 0, min(n, total)
        if li > total:
            li, fi = total, max(0, total - n)
        return fi, li

    def wheelEvent(self, ev: QWheelEvent) -> None:
        """Scroll through octaves with the mouse wheel."""
        delta = ev.angleDelta().y()
        if delta > 0:
            # scroll right → shift up by a white key
            idx = self._white_midis.index(self._scroll_midi)
            self._scroll_midi = self._white_midis[min(idx + 3, len(self._white_midis) - 1)]
        elif delta < 0:
            idx = self._white_midis.index(self._scroll_midi)
            self._scroll_midi = self._white_midis[max(idx - 3, 0)]
        self.update()
        ev.accept()

    # ── Painting ───────────────────────────────────────────────────────────

    def paintEvent(self, ev: QPaintEvent) -> None:  # noqa: D401
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return

        # Scale black‑key height to widget height
        kw = _WW
        kh = float(h - 4)
        bw = _BW
        bh = _BH * (h / _TH) if h > 0 else _BH

        fi, li = self._visible_range()
        vw = self._white_midis[fi:li]       # visible white keys
        lo = vw[0] if vw else 60
        hi = self._white_midis[li - 1] if li > fi else 71

        # ── White keys ─────────────────────────────────────────────────
        label_font = QFont("Sans", 9)
        for i, midi in enumerate(vw):
            x = i * kw + 2
            y = 2.0
            r = QRectF(x, y, kw - 2, kh)
            pc = midi % 12

            # Colour priority: bass > chord > scale > default
            if midi == self._bass_midi and midi in self._hl:
                fl = _CHB                       # green – bass
            elif midi in self._hl:
                fl = self._hl[midi]             # gold (or custom) – chord
            elif pc in self._sp:
                fl = _CHS                       # blue – scale only
            else:
                fl = _CW                        # white

            p.setBrush(QBrush(fl))
            p.setPen(QPen(_CBD, 2.0))
            p.drawRoundedRect(r, 2, 2)

            # ── Octave label on C keys ─────────────────────────────────
            if pc == 0:
                octave = midi // 12 - 1         # MIDI note 60 → C4
                label = f"C{octave}"
                p.setFont(label_font)
                p.setPen(QPen(_CT, 1))
                fm = QFontMetrics(label_font)
                tw = fm.horizontalAdvance(label)
                tx = x + (kw - 2 - tw) - 4      # right‑aligned inside the key
                ty = y + kh - fm.height() - 2     # near the bottom
                p.drawText(QPointF(tx, ty + fm.ascent()), label)

        # ── Black keys ─────────────────────────────────────────────────
        for midi in self._black_midis:
            if midi < lo - 1 or midi > hi + 1:
                continue
            left_white = midi - 1
            if left_white not in self._white_midis:
                continue
            full_wi = self._white_midis.index(left_white)
            wi = full_wi - fi
            if wi < 0 or wi >= len(vw) - 1:
                continue

            x = (wi + 1) * kw + 1 - bw / 2
            y = 2.0
            r = QRectF(x, y, bw, bh)
            pc = midi % 12

            # Colour priority (same as white keys, dark variants)
            if midi == self._bass_midi and midi in self._hl:
                fl = _CHBB                       # dark green – bass
            elif midi in self._hl:
                fl = _CHCB                       # dark gold – chord
            elif pc in self._sp:
                fl = _CHSB                       # dark blue – scale
            else:
                fl = _CB                         # black

            pen = QPen(_CBG, 2.0) if midi in self._hl else QPen(QColor(0, 0, 0, 0), 0)
            p.setBrush(QBrush(fl))
            p.setPen(pen)
            p.drawRoundedRect(r, 2, 2)

    # ── Mouse interaction ─────────────────────────────────────────────────

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        midi = self._midi_at(ev.position().x(), ev.position().y())
        if midi is not None:
            if midi in self._hl:
                del self._hl[midi]
            else:
                self._hl[midi] = _CHC
            self.update()
            self.noteClicked.emit(midi, _midi_name(midi))

    def _midi_at(self, mx: float, my: float) -> int | None:
        """Return the MIDI note at viewport position *(mx, my)*, or ``None``."""
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            return None
        kw = _WW
        kh = float(h - 4)
        bw = _BW
        bh = _BH * (h / _TH) if h > 0 else _BH
        fi, li = self._visible_range()
        vw = self._white_midis[fi:li]
        lo = vw[0] if vw else 60
        hi = self._white_midis[li - 1] if li > fi else 71

        # Check black keys first (they sit on top)
        for midi in self._black_midis:
            if midi < lo - 1 or midi > hi + 1:
                continue
            left_white = midi - 1
            if left_white not in self._white_midis:
                continue
            full_wi = self._white_midis.index(left_white)
            wi = full_wi - fi
            if wi < 0 or wi >= len(vw) - 1:
                continue
            x = (wi + 1) * kw + 1 - bw / 2
            y = 2.0
            if x <= mx <= x + bw and y <= my <= y + bh:
                return midi

        # Then white keys
        for i, midi in enumerate(vw):
            x = i * kw + 2
            y = 2.0
            if x <= mx <= x + kw - 2 and y <= my <= y + kh:
                return midi

        return None


# ── Helpers ────────────────────────────────────────────────────────────────────

def _midi_name(midi: int) -> str:
    """Return human‑readable note name, e.g. ``"C4"`` for MIDI 60."""
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


# ═══════════════════════════════════════════════════════════════════════════════
# ── Demo ──────────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

# Chord + scale helpers for the demo
_CHORDS: dict[str, list[int]] = {
    "C major":  [60, 64, 67],          # C  E  G
    "D minor":  [62, 65, 69],          # D  F  A
    "F major":  [65, 69, 72],          # F  A  C
    "G7":       [67, 71, 74, 77],      # G  B  D  F
    "Am":       [69, 72, 76],          # A  C  E
}

_SCALES: dict[str, list[int]] = {
    "C major":  [60, 62, 64, 65, 67, 69, 71, 72],
    "C minor":  [60, 62, 63, 65, 67, 68, 70, 72],
}


class PianoDemo(QWidget):
    """Interactive demo that cycles through chords, scales, and bass notes."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Piano Keyboard – PySide6 (Feature Demo)")
        self.resize(1012, 340)
        self.setStyleSheet("background-color:#1a1a2e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Info label ──────────────────────────────────────────────────
        self._info = QLabel("Ready – use scroll wheel to pan | click keys to toggle")
        self._info.setStyleSheet(
            "color:#a0a5c0; font-size:13px; padding:4px 8px; "
            "background:#22223a; border-radius:4px;"
        )
        self._info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._info)

        # ── Piano widget ────────────────────────────────────────────────
        self.pn = PianoWidget()
        self.pn.setStyleSheet("border:1px solid #505060; border-radius:4px;")
        layout.addWidget(self.pn, stretch=1)

        self.pn.noteClicked.connect(self._on_note_clicked)

        # ── Control buttons ─────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_style = (
            "QPushButton { background:#2a2a4a; color:#c0c5e0; border:1px solid #505070; "
            "border-radius:4px; padding:6px 14px; font-size:12px; } "
            "QPushButton:hover { background:#3a3a6a; } "
            "QPushButton:pressed { background:#4a4a7a; }"
        )

        buttons: list[tuple[str, t.Callable[[], None]]] = [
            ("C Major Chord",  lambda: self._demo_chord("C major")),
            ("D Minor Chord",  lambda: self._demo_chord("D minor")),
            ("F Major Chord",  lambda: self._demo_chord("F major")),
            ("G7 Chord",       lambda: self._demo_chord("G7")),
            ("Am Chord",       lambda: self._demo_chord("Am")),
            ("C Major Scale",  lambda: self._demo_scale("C major")),
            ("C Minor Scale",  lambda: self._demo_scale("C minor")),
            ("Clear All",      self._demo_clear),
        ]

        for label, cb in buttons:
            btn = QPushButton(label)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(cb)
            btn_row.addWidget(btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # ── Start auto‑demo timer ───────────────────────────────────────
        self._demo_states: list[t.Callable[[], None]] = [
            lambda: self._demo_full("C major", "C major", bass=60),
            lambda: self._demo_full("D minor", "C major", bass=62),
            lambda: self._demo_full("F major", "C major", bass=65),
            lambda: self._demo_full("G7",      "C major", bass=67),
            lambda: self._demo_full("Am",      "C major", bass=69),
            lambda: self._demo_full("C major", "C minor", bass=60),
        ]
        self._demo_idx = 0
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._next_auto_demo)
        self._auto_timer.start(3000)            # cycle every 3 seconds

        # Kick off the first demo state
        self._demo_states[0]()

    # ── Button handlers ──────────────────────────────────────────────────

    def _demo_chord(self, name: str) -> None:
        midis = _CHORDS[name]
        self.pn.clear_all()
        self.pn.highlight_notes(midis)
        self.pn.set_bass_note(midis[0])
        self._update_info(f"Chord: {name}  |  bass: {_midi_name(midis[0])}")

    def _demo_scale(self, name: str) -> None:
        midis = _SCALES[name]
        self.pn.clear_all()
        self.pn.set_scale_pcs(midis)
        self._update_info(f"Scale: {name}  (no chord, no bass)")

    def _demo_full(self, chord_name: str, scale_name: str, bass: int) -> None:
        chord_midis = _CHORDS[chord_name]
        scale_midis = _SCALES[scale_name]
        self.pn.clear_all()
        self.pn.highlight_notes(chord_midis)
        self.pn.set_scale_pcs(scale_midis)
        self.pn.set_bass_note(bass)
        self._update_info(
            f"Chord: {chord_name}  |  Scale: {scale_name}  |  Bass: {_midi_name(bass)}"
        )

    def _demo_clear(self) -> None:
        self.pn.clear_all()
        self._update_info("Cleared – all keys reset")

    def _next_auto_demo(self) -> None:
        self._demo_states[self._demo_idx]()
        self._demo_idx = (self._demo_idx + 1) % len(self._demo_states)

    def _update_info(self, text: str) -> None:
        self._info.setText(f"  {text}  |  🖱 scroll to pan  |  🖱 click keys to toggle")

    def _on_note_clicked(self, midi: int, name: str) -> None:
        print(f"Note clicked: {name} (MIDI={midi})")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = PianoDemo()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

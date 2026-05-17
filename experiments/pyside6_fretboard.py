"""
PySide6 Guitar Fretboard Widget — enhanced to match all DPG features.

Supports:
  - Dual display modes: "fret" (fret numbers, root gold) / "note" (note names, root green)
  - Chord shape loading via set_chord_shape(diagram, root_pc)
  - Open string circles ("O") and muted string marks ("X")
  - Root note highlighting (gold in fret mode, green in note mode)
  - Interactive mouse: hover highlight ring, click to toggle dots
  - MiniFretboardWidget (compact non-interactive preview)
  - String labels at bottom, fret-position labels, start-fret indicator
  - Fully self-contained — no dearpygui imports
"""
from __future__ import annotations

import sys
import typing as t
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import (
    QBrush, QColor, QFont, QFontMetrics, QPainter, QPen,
)
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Exported constants (backward-compatible)
# ═══════════════════════════════════════════════════════════════════════════════

STRING_NAMES  = ["E", "A", "D", "G", "B", "e"]
CHROMATIC     = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
OPEN_PITCHES  = [4, 9, 2, 7, 11, 4]   # low-E … high-e

# ═══════════════════════════════════════════════════════════════════════════════
# Colour palette (Catppuccin Mocha-inspired)
# ═══════════════════════════════════════════════════════════════════════════════

C_BG          = QColor("#F5F0E8")     # warm cream
C_FRET_LINE   = QColor("#C4A882")     # warm tan
C_NUT         = QColor("#5A412D")     # darker warm brown
C_STRING      = QColor("#8B6F4E")     # warm brown
C_DOT         = QColor("#D4C5B0")     # warm tan
C_ROOT_GOLD   = QColor(232, 180, 80)   # warm gold
C_ROOT_GREEN  = QColor(122, 154, 85)   # warm olive green
C_MUTED       = QColor(200, 80, 60)    # warm red
C_OPEN        = QColor(122, 154, 85)   # warm olive green
C_TEXT        = QColor("#4A3728")     # warm dark brown
C_TEXT_DIM    = QColor("#8B7355")     # warm medium brown
C_DOT_TEXT    = QColor(245, 240, 232)  # warm cream on dots
C_HOVER       = QColor("#E8A850")     # warm amber outline
C_FRET_MARKER = QColor(180, 160, 135)  # warm tan marker
C_START_FRET  = QColor("#8B7355")     # warm medium brown


# ═══════════════════════════════════════════════════════════════════════════════
# FretboardWidget — full interactive widget
# ═══════════════════════════════════════════════════════════════════════════════

class FretboardWidget(QWidget):
    """Interactive six-string guitar fretboard (frets 0–12)."""

    noteClicked = Signal(int, int, int)   # string_index, fret, pitch_class

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(400, 160)
        self.setSizePolicy(QSizePolicy.MinimumExpanding,
                           QSizePolicy.MinimumExpanding)
        self.setMouseTracking(True)

        # data
        self._shape: dict[int, t.Optional[int]] = {}   # string_idx → fret
        self._root_pc: t.Optional[int] = None
        self._mode: str = "fret"                        # "fret" | "note"

        # highlight / hover
        self._hl: dict[tuple[int, int], QColor] = {}
        self._hover_string: t.Optional[int] = None
        self._hover_fret: t.Optional[int] = None

        # layout margins
        self._ml = 60   # left
        self._mr = 20   # right
        self._mt = 0    # top
        self._mb = 50   # bottom (string names + fret numbers)

    # ── Public API ────────────────────────────────────────────────────────

    def set_mode(self, mode: str) -> None:
        """Set display mode: 'fret' (fret numbers) or 'note' (note names).

        In fret mode the root is highlighted gold; in note mode it is green.
        """
        if mode in ("fret", "note"):
            self._mode = mode
            self.update()

    def get_mode(self) -> str:
        """Return the current display mode."""
        return self._mode

    def set_chord_shape(self,
                        diagram: list[tuple[int, t.Optional[int]]],
                        root_pc: int = 0) -> None:
        """Load a chord shape from DPG-compatible data.

        *diagram* is a list of ``(string_index, fret)`` tuples where
        ``fret`` may be ``None`` (muted), ``0`` (open), or ``> 0`` (fretted).
        *root_pc* is the pitch-class (0–11) of the chord root for highlighting.
        """
        self._shape.clear()
        for si, fret in diagram:
            if 0 <= si < 6:
                self._shape[si] = fret
        self._root_pc = root_pc
        self.update()

    def clear_dots(self) -> None:
        """Remove all dots from the fretboard."""
        self._shape.clear()
        self._root_pc = None
        self.update()

    def set_root_pc(self, pc: int) -> None:
        """Set the root pitch-class used for highlighting."""
        self._root_pc = pc
        self.update()

    def highlight_pc(self, pc: int, color: QColor | None = None) -> None:
        """Highlight every position matching *pc* (0–11)."""
        if color is None:
            color = C_ROOT_GOLD
        for st in range(6):
            for fr in range(13):
                if ((OPEN_PITCHES[st] + fr) % 12) == pc:
                    self._hl[(st, fr)] = color
        self.update()

    def highlight_notes(self,
                         pcs: list[int],
                         color: QColor | None = None) -> None:
        """Highlight positions matching any pitch-class in *pcs*."""
        if color is None:
            color = C_ROOT_GOLD
        ps = set(pcs)
        for st in range(6):
            for fr in range(13):
                if ((OPEN_PITCHES[st] + fr) % 12) in ps:
                    self._hl[(st, fr)] = color
        self.update()

    def clear_highlights(self) -> None:
        """Remove all highlights."""
        self._hl.clear()
        self.update()

    def clear_all(self) -> None:
        """Clear highlights and root."""
        self._hl.clear()
        self._root_pc = None
        self.update()

    def pc_at(self, string: int, fret: int) -> int:
        """Pitch-class at *string* / *fret* (0–11)."""
        return (OPEN_PITCHES[string] + fret) % 12

    def get_shape(self) -> dict[int, t.Optional[int]]:
        """Return a copy of the current chord shape dict."""
        return dict(self._shape)

    def has_dot(self, string: int, fret: int) -> bool:
        """``True`` if a dot is set at the given position."""
        return self._shape.get(string) == fret

    # ── Fret-range helper ─────────────────────────────────────────────────

    def _fret_range(self) -> tuple[int, int]:
        """Return ``(start_fret, fret_count)`` for the current shape."""
        if not self._shape:
            return 0, 5
        frets = [f for f in self._shape.values()
                 if f is not None and f > 0]
        if not frets:
            return 0, 5
        min_f = min(frets)
        max_f = max(frets)
        has_open = any(f == 0 for f in self._shape.values() if f is not None)
        start_fret = 0 if has_open else max(1, min_f)
        fret_count = min(5, max_f - start_fret + 2)
        return start_fret, fret_count

    # ── Geometry helpers ──────────────────────────────────────────────────

    def _string_y(self, si: int, sp: float) -> float:
        """Y-coordinate of string *si* (0 = low E, bottom)."""
        return self._mt + sp * 5.5 - si * sp

    def _fret_x(self, fi: float, fp: float) -> float:
        """X-coordinate of fret-line *fi* — real-guitar geometric spacing."""
        if fi <= 0:
            return self._ml
        total_w = self.width() - self._ml - self._mr
        L = 2 * total_w            # scale length → fret 12 at right edge
        return self._ml + L * (1 - 2 ** (-fi / 12))

    def _dot_x(self, fret: int, fp: float) -> float:
        """X-centre of fret *fret* space (midpoint between adjacent fret lines)."""
        if fret <= 0:
            return self._ml                     # open‑string indicator at nut
        return (self._fret_x(fret - 1, fp) + self._fret_x(fret, fp)) / 2

    def _layout(self) -> tuple[float, float]:
        """Return ``(string_spacing, fret_spacing)`` from widget size."""
        w, h = self.width(), self.height()
        fp = (w - self._ml - self._mr) / 12.0 if w > 70 else 20.0
        sp = (h - self._mt - self._mb) / 5.0 if h > 75 else 20.0
        return sp, fp

    def _fret_centers(self, fp: float) -> list[tuple[int, float]]:
        """Return ``[(fret_idx, centre_x), …]`` for fret spaces 1–12."""
        out = []
        for n in range(1, 13):
            out.append((n, (self._fret_x(n - 1, fp) + self._fret_x(n, fp)) / 2))
        return out

    # ── Paint ─────────────────────────────────────────────────────────────

    def paintEvent(self, event):  # noqa: C901
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), C_BG)

        ss, fs = self._layout()
        fbh = self.height() - self._mt - self._mb        # fretboard height
        total_frets = 13                                  # 0 (nut) … 12

        # derived sizes
        nut_lw  = max(2, min(8, fs * 0.07))
        fret_lw = max(0.6, min(3, fs * 0.025))
        str_lw  = max(0.5, min(3, fs * 0.02))
        fn_fs   = max(7, min(16, int(fs * 0.18)))        # fret-number font
        sn_fs   = max(8, min(18, int(ss * 0.45)))        # string-name font
        dt_fs   = max(5, min(14, int(min(ss, fs) * 0.32)))  # dot-label font
        dot_r   = max(4, min(16, int(min(ss, fs) * 0.32)))  # dot radius
        mk_r    = max(3, min(8, fs * 0.09))              # marker radius
        mk_off  = ss * 0.5                               # 12th-fret marker offset

        start_fret, _fret_count = self._fret_range()

        # fret lines (vertical) — flush with outer strings
        fret_top = self._string_y(5, ss)   # high e (top)
        fret_bot = self._string_y(0, ss)   # low E (bottom)
        for fr in range(total_frets):
            x = self._fret_x(fr, fs)
            if fr == 0 and start_fret == 0:
                pen = QPen(C_NUT, nut_lw)                 # nut — thick line
            else:
                pen = QPen(C_FRET_LINE, fret_lw)
            p.setPen(pen)
            p.drawLine(int(x), int(fret_top),
                       int(x), int(fret_bot))

        # strings (horizontal)
        p.setPen(QPen(C_STRING, str_lw))
        for st in range(6):
            y = self._string_y(st, ss)
            p.drawLine(int(self._ml), int(y),
                       int(self._fret_x(12, fs)), int(y))

        # fret-position labels (bottom) — centred under each fret space
        p.setFont(QFont("Consolas", fn_fs))
        p.setPen(C_TEXT)
        for fr in range(total_frets):
            label = str(fr)
            fm = QFontMetrics(p.font())
            cx = self._dot_x(fr, fs)
            p.drawText(
                QPointF(int(cx) - fm.horizontalAdvance(label) // 2,
                        int(self._string_y(0, ss) + ss * 0.85)),
                label,
            )
        # start-fret indicator (when > 0)
        if start_fret > 0:
            p.setFont(QFont("Consolas", max(10, fn_fs)))
            p.setPen(C_START_FRET)
            p.drawText(
                QPointF(self._ml - 18,
                        self._mt + fbh / 2 + fn_fs * 0.3),
                str(start_fret),
            )

        # string-name labels with open/muted indicators
        p.setFont(QFont("Consolas", sn_fs, QFont.Weight.Bold))
        for st in range(6):
            y_base = self._string_y(st, ss)
            letter = STRING_NAMES[st]
            fret = self._shape.get(st)

            fm = QFontMetrics(p.font())
            lw = fm.horizontalAdvance(letter)
            lh = fm.height()
            text_x = 18
            text_y = y_base + sn_fs * 0.35
            cx = text_x + lw / 2 + 1.0
            cy = text_y - fm.ascent() * 0.40 + 1
            cr = max(lw, lh) / 2 + 5

            if fret is None:           # muted: thin red X
                p.setPen(QPen(C_MUTED, 1.5))
                d = cr * 0.65
                p.drawLine(QPointF(int(cx - d), int(cy - d)),
                           QPointF(int(cx + d), int(cy + d)))
                p.drawLine(QPointF(int(cx + d), int(cy - d)),
                           QPointF(int(cx - d), int(cy + d)))
            elif fret == 0:            # open: green filled circle
                p.setPen(QPen(C_OPEN, 1.5))
                p.setBrush(QBrush(QColor(60, 210, 100, 60)))
                p.drawEllipse(QPointF(cx, cy), cr, cr)

            # letter on top
            p.setPen(C_TEXT)
            p.drawText(QPointF(text_x, int(y_base + sn_fs * 0.35)), letter)

        # fretboard position markers (3, 5, 7, 9, 12)
        p.setBrush(QBrush(C_FRET_MARKER))
        p.setPen(QPen(QColor(0, 0, 0, 0), 0))
        cy = (self._string_y(0, ss) + self._string_y(5, ss)) / 2
        for fr in (3, 5, 7, 9):
            p.drawEllipse(QPointF(self._dot_x(fr, fs), cy), mk_r, mk_r)
        mx12 = self._dot_x(12, fs)
        p.drawEllipse(QPointF(mx12, cy - mk_off), mk_r, mk_r)
        p.drawEllipse(QPointF(mx12, cy + mk_off), mk_r, mk_r)

        # chord-shape dots
        p.setFont(QFont("Consolas", dt_fs, QFont.Weight.Bold))
        for si in range(6):
            fret = self._shape.get(si)
            if fret is None or fret == 0:      # open/muted — drawn on string labels
                continue

            y_str = self._string_y(si, ss)

            # fretted
            npc = (OPEN_PITCHES[si] + fret) % 12
            is_root = (self._root_pc is not None and npc == self._root_pc)
            key = (si, fret)

            if key in self._hl:
                dot_color = self._hl[key]
            elif is_root:
                dot_color = (C_ROOT_GREEN if self._mode == "note"
                             else C_ROOT_GOLD)
            else:
                dot_color = C_DOT

            cx = self._dot_x(fret, fs)
            p.setBrush(QBrush(dot_color))
            p.setPen(QPen(QColor(0, 0, 0, 0), 0))
            p.drawEllipse(QPointF(cx, y_str), dot_r, dot_r)

            if self._mode == "note":
                label = CHROMATIC[npc]
            else:
                label = str(fret)

            p.setPen(C_DOT_TEXT)
            fm = QFontMetrics(p.font())
            p.drawText(
                QPointF(int(cx) - fm.horizontalAdvance(label) // 2,
                        int(y_str + dt_fs * 0.35)),
                label,
            )

        # hover ring
        if self._hover_string is not None and self._hover_fret is not None:
            if self._hover_fret == 0:
                # label area — centre under the string letter
                fm_sn = QFontMetrics(QFont("Consolas", sn_fs, QFont.Weight.Bold))
                letter = STRING_NAMES[self._hover_string]
                lw = fm_sn.horizontalAdvance(letter)
                cx = 18 + lw / 2 + 1.0
                y_base = self._string_y(self._hover_string, ss)
                cy = y_base + sn_fs * 0.35 - fm_sn.ascent() * 0.40 + 1
            else:
                cx = self._dot_x(self._hover_fret, fs)
                cy = self._string_y(self._hover_string, ss)
            r = min(ss, fs) * 0.38
            p.setPen(QPen(C_HOVER, max(1.5, min(4, fs * 0.03))))
            p.setBrush(Qt.NoBrush)
            p.drawEllipse(QPointF(cx, cy), r, r)

        p.end()

    # ── Mouse interaction ─────────────────────────────────────────────────

    def _hit_test(self,
                  pos: QPointF) -> tuple[t.Optional[int], t.Optional[int]]:
        """Return ``(string_idx, fret)`` under *pos*, or ``(None, None)``."""
        ss, fs = self._layout()

        # fret — nearest fret-space centre (geometric spacing)
        x = pos.x()
        centers = self._fret_centers(fs)
        best_fr, best_dist = None, float("inf")
        for fr, cx in centers:
            d = abs(x - cx)
            if d < best_dist:
                best_fr, best_dist = fr, d

        # dynamic margin based on local fret spacing
        if best_fr is not None and 1 < best_fr < 12:
            local_fs = (self._fret_x(best_fr + 1, fs) - self._fret_x(best_fr - 1, fs)) / 2
        elif best_fr == 1:
            local_fs = (self._fret_x(2, fs) - self._ml) / 2
        else:
            local_fs = fs
        mg = max(4, min(12, local_fs * 0.12))
        if best_dist > local_fs * 0.35 + mg:
            best_fr = None

        # label area (left of first fret space): map click to fret 0
        if best_fr is None and x < self._ml:
            best_fr = 0

        # string (inverted: 0=bottom low-E, 5=top high-e)
        y = pos.y()
        st = 5 - int((y - self._mt) / ss) if ss > 0 else 0
        st = max(0, min(5, st))
        cy = self._string_y(st, ss)
        if abs(y - cy) > ss * 0.45 + mg:
            st = None

        return st, best_fr

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            si, fr = self._hit_test(event.position())
            if si is not None and fr is not None:
                if fr == 0:
                    # label click — cycle: None → 0 → None
                    cur = self._shape.get(si)
                    self._shape[si] = 0 if cur != 0 else None
                else:
                    # toggle: if already set → remove; otherwise → set
                    if self._shape.get(si) == fr:
                        del self._shape[si]
                    else:
                        self._shape[si] = fr
                self.noteClicked.emit(si, fr, self.pc_at(si, fr))
                self.update()

    def mouseMoveEvent(self, event) -> None:
        self._hover_string, self._hover_fret = self._hit_test(event.position())
        self.update()

    def leaveEvent(self, event) -> None:
        self._hover_string = None
        self._hover_fret = None
        self.update()


# ═══════════════════════════════════════════════════════════════════════════════
# MiniFretboardWidget — compact non-interactive preview
# ═══════════════════════════════════════════════════════════════════════════════

class MiniFretboardWidget(QWidget):
    """Compact 115×90 px fretboard thumbnail — non-interactive, DPG-style."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(115, 90)
        self._shape: dict[int, t.Optional[int]] = {}
        self._root_pc: t.Optional[int] = None
        self._mode: str = "fret"

    # ── Public API ────────────────────────────────────────────────────────

    def set_chord_shape(self,
                        diagram: list[tuple[int, t.Optional[int]]],
                        root_pc: int = 0) -> None:
        """Load a chord shape (same format as FretboardWidget)."""
        self._shape.clear()
        for si, fret in diagram:
            if 0 <= si < 6:
                self._shape[si] = fret
        self._root_pc = root_pc
        self.update()

    def set_mode(self, mode: str) -> None:
        """Set display mode: 'fret' or 'note'."""
        if mode in ("fret", "note"):
            self._mode = mode
            self.update()

    def clear_dots(self) -> None:
        """Remove all dots."""
        self._shape.clear()
        self._root_pc = None
        self.update()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _fret_range(self) -> tuple[int, int]:
        if not self._shape:
            return 0, 5
        frets = [f for f in self._shape.values()
                 if f is not None and f > 0]
        if not frets:
            return 0, 5
        min_f = min(frets)
        max_f = max(frets)
        has_open = any(f == 0 for f in self._shape.values() if f is not None)
        start_fret = 0 if has_open else max(1, min_f)
        fret_count = min(5, max_f - start_fret + 2)
        return start_fret, fret_count

    # ── Paint ─────────────────────────────────────────────────────────────

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), C_BG)

        W, H = self.width(), self.height()
        str_gap = 12
        x0 = (W - 5 * str_gap) // 2        # centred horizontally
        y0 = 22

        start_fret, fret_count = self._fret_range()
        fret_gap = (H - 28) / max(fret_count, 3)

        # frets
        for f in range(fret_count + 1):
            y = y0 + f * fret_gap
            thickness = 3 if f == 0 else 1
            colour = (C_START_FRET if (f == 0 and start_fret == 0)
                      else C_STRING)
            p.setPen(QPen(colour, thickness))
            p.drawLine(int(x0), int(y),
                       int(x0 + 5 * str_gap), int(y))
            if f == 0 and start_fret > 0:
                p.setPen(C_START_FRET)
                p.setFont(QFont("Consolas", 10))
                p.drawText(QPointF(int(x0 - 15), int(y0 - 2)),
                           str(start_fret))

        # strings
        p.setPen(QPen(C_STRING, 1))
        for s in range(6):
            x = x0 + s * str_gap
            p.drawLine(int(x), int(y0),
                       int(x), int(y0 + fret_count * fret_gap))

        # dots
        for si in range(6):
            fret = self._shape.get(si)
            x = x0 + si * str_gap

            if fret is None:                     # muted
                p.setPen(C_MUTED)
                p.setFont(QFont("Consolas", 8))
                p.drawText(QPointF(int(x) - 3, int(y0 - 6)), "X")

            elif fret == 0:                      # open
                p.setPen(C_OPEN)
                p.setFont(QFont("Consolas", 8))
                p.drawText(QPointF(int(x) - 3, int(y0 - 6)), "O")

            else:                                # fretted
                dot_y = y0 + (fret - max(start_fret, 1)) * fret_gap
                cy = dot_y + fret_gap / 2
                npc = (OPEN_PITCHES[si] + fret) % 12
                is_root = (self._root_pc is not None and npc == self._root_pc)

                if self._mode == "note":
                    dc = C_ROOT_GREEN if is_root else C_DOT
                else:
                    dc = C_ROOT_GOLD if is_root else C_DOT

                p.setBrush(QBrush(dc))
                p.setPen(QPen(QColor(0, 0, 0, 0), 0))
                p.drawEllipse(QPointF(x, cy), 4, 4)

        p.end()


# ═══════════════════════════════════════════════════════════════════════════════
# FretboardDemo — test harness exercising every feature
# ═══════════════════════════════════════════════════════════════════════════════

class FretboardDemo(QWidget):
    """Demo window: full widget + mini preview + mode toggle + chord presets."""

    # Pre-loaded chord shapes — DPG-compatible (string_idx, fret)
    # string_idx: 0=low E … 5=high e
    PRESETS: t.ClassVar[list[tuple[str, list[tuple[int, t.Optional[int]]], int]]] = [
        # string_idx: 0=low E … 5=high e   root_pc: C=0 D=2 E=4 F=5 G=7 A=9
        ("C Major", [
            (0, None), (1, 3), (2, 2), (3, 0), (4, 1), (5, 0),
        ], 0),
        ("A Minor", [
            (0, None), (1, 0), (2, 2), (3, 2), (4, 1), (5, 0),
        ], 9),
        ("G Major", [
            (0, 3), (1, 2), (2, 0), (3, 0), (4, 0), (5, 3),
        ], 7),
        ("D Major", [
            (0, None), (1, None), (2, 0), (3, 2), (4, 3), (5, 2),
        ], 2),
        ("E Major", [
            (0, 0), (1, 2), (2, 2), (3, 1), (4, 0), (5, 0),
        ], 4),
        ("F Major", [
            (0, 1), (1, 3), (2, 3), (3, 2), (4, 1), (5, 1),
        ], 5),
        ("E Minor", [
            (0, 0), (1, 2), (2, 2), (3, 0), (4, 0), (5, 0),
        ], 4),
        ("D Minor", [
            (0, None), (1, None), (2, 0), (3, 2), (4, 3), (5, 1),
        ], 2),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Guitar Fretboard — PySide6 (Enhanced)")
        self.resize(900, 500)

        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(30, 30, 30, 30)
        root_lay.setSpacing(4)

        # main fretboard
        self.fb = FretboardWidget()
        root_lay.addWidget(self.fb, 1)

        # mini preview row
        mini_row = QHBoxLayout()
        mini_row.setContentsMargins(10, 4, 10, 0)
        lbl = QLabel("Mini previews:")
        lbl.setStyleSheet("color:#8B7355; font-family:Consolas; font-size:10px;")
        mini_row.addWidget(lbl)

        self.minis: list[MiniFretboardWidget] = []
        for name, shape, rpc in self.PRESETS[:4]:   # first 4 as mini previews
            mfw = MiniFretboardWidget()
            mfw.set_chord_shape(shape, rpc)
            mfw.setToolTip(name)
            self.minis.append(mfw)
            mini_row.addWidget(mfw)
        mini_row.addStretch()
        root_lay.addLayout(mini_row)

        # control bar
        bar = QHBoxLayout()
        bar.setContentsMargins(10, 6, 10, 6)

        self.info = QLabel("Mode: fret  |  Dots: 3  |  Click any fret to toggle")
        self.info.setStyleSheet("color:#8B7355; font-family:Consolas; font-size:11px;")
        bar.addWidget(self.info)

        btn_style = (
            "QPushButton { background:#EDE4D3; color:#4A3728; "
            "border:1px solid #D4C5B0; padding:4px 10px; "
            "font-family:Consolas; font-size:11px; }"
            "QPushButton:hover { background:#E1D6C3; }"
        )

        # mode toggle
        self.mode_btn = QPushButton("Toggle: Note Mode")
        self.mode_btn.setStyleSheet(btn_style)
        self.mode_btn.clicked.connect(self._toggle_mode)
        bar.addWidget(self.mode_btn)
        bar.addSpacing(8)

        # chord preset buttons
        for name, shape, rpc in self.PRESETS:
            btn = QPushButton(name)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(
                lambda checked, s=shape, r=rpc: (
                    self.fb.set_chord_shape(s, r),
                    self._update_info(),
                )
            )
            bar.addWidget(btn)

        bar.addSpacing(8)

        # clear button
        clr = QPushButton("Clear")
        clr.setStyleSheet(
            "QPushButton { background:#E1D6C3; color:#f38ba8; "
            "border:1px solid #D4C5B0; padding:4px 10px; "
            "font-family:Consolas; font-size:11px; }"
            "QPushButton:hover { background:#D4C5B0; }"
        )
        clr.clicked.connect(lambda: (self.fb.clear_dots(), self._update_info()))
        bar.addWidget(clr)

        bar.addStretch()
        root_lay.addLayout(bar)

        # initial chord
        name, shape, rpc = self.PRESETS[0]
        self.fb.set_chord_shape(shape, rpc)

        self.setStyleSheet("background-color:#F5F0E8;")
        self.fb.noteClicked.connect(lambda *_: self._update_info())

    def _toggle_mode(self) -> None:
        current = self.fb.get_mode()
        new_mode = "note" if current == "fret" else "fret"
        self.fb.set_mode(new_mode)
        self.mode_btn.setText(
            "Toggle: Note Mode" if new_mode == "fret" else "Toggle: Fret Mode"
        )
        self._update_info()

    def _update_info(self) -> None:
        mode = self.fb.get_mode()
        shape = self.fb.get_shape()
        dot_count = sum(1 for f in shape.values() if f is not None and f > 0)
        self.info.setText(
            f"Mode: {mode}  |  Dots: {dot_count}  |  Click any fret to toggle"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    p = app.palette()
    p.setColor(p.ColorRole.Window, QColor("#F5F0E8"))
    p.setColor(p.ColorRole.WindowText, QColor("#4A3728"))
    app.setPalette(p)

    w = FretboardDemo()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

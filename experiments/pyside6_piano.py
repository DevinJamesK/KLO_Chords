"""PySide6 Piano Keyboard Widget — scrollable multi‑octave piano with chord / scale / bass highlighting"""
from __future__ import annotations
import sys, typing as t
from PySide6.QtCore import Qt, Signal, QRectF, QSize, QTimer
from PySide6.QtGui import *
from PySide6.QtWidgets import *

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
_MLO, _MHI = 21, 108          # full 88‑key MIDI range A0‑C8
_WPC = {0,2,4,5,7,9,11}
_BPC = {1,3,6,8,10}
_WW, _WH = 48.0, 160.0
_BW, _BH = 30.0, 100.0
_TH = _WH + 4
_CW =QColor(255,255,255);_CB =QColor(24,24,28);_CBD=QColor(40,40,50)
_CHC=QColor(255,210,50);_CHS=QColor(100,180,255);_CHB=QColor(80,230,80)
_CHCB=QColor(200,160,30);_CHSB=QColor(40,80,180);_CHBB=QColor(40,180,40)
_CT =QColor(20,20,30);_CBG=QColor(26,26,46)

class PianoWidget(QWidget):
    noteClicked=Signal(int,str)
    def __init__(s,parent=None):
        super().__init__(parent)
        s.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
        s.setMinimumSize(340,200); s.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        s._hl={}; s._sp=set(); s._bass=-1; s._scroll=60
        s._wm=[m for m in range(_MLO,_MHI+1) if m%12 in _WPC]
        s._bm=[m for m in range(_MLO,_MHI+1) if m%12 in _BPC]
    def highlight_note(s,midi,color=None):
        if color is None:color=_CHC
        s._hl[midi]=color; s.update()
    def highlight_notes(s,midis,color=None):
        if color is None:color=_CHC
        for m in midis:s._hl[m]=color
        s.update()
    def set_scale_pcs(s,midis):
        s._sp={m%12 for m in midis}; s.update()
    def set_bass_note(s,midi):
        s._bass=midi; s.update()
    def clear_highlights(s):
        s._hl.clear(); s.update()
    def clear_all(s):
        s._hl.clear(); s._sp.clear(); s._bass=-1; s.update()
    def sizeHint(s):return QSize(52*48+4,200)
    def minimumSizeHint(s):return QSize(340,200)
    def _visible_range(s):
        w=s.width(); n=max(7,int(w//_WW))
        try:ci=s._wm.index(s._scroll)
        except ValueError:ci=0
        fi=ci-n//2;li=fi+n;t=len(s._wm)
        if fi<0:fi=0;li=min(n,t)
        if li>t:li=t;fi=max(0,t-n)
        return fi,li
    def wheelEvent(s,ev):
        d=ev.angleDelta().y()
        if d>0:idx=s._wm.index(s._scroll);s._scroll=s._wm[min(idx+3,len(s._wm)-1)]
        elif d<0:idx=s._wm.index(s._scroll);s._scroll=s._wm[max(idx-3,0)]
        s.update();ev.accept()
    def paintEvent(s,ev):
        p=QPainter(s);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=s.width(),s.height()
        if w<=0 or h<=0:return
        kw=_WW;kh=float(h-4);bw=_BW;bh=_BH*(h/_TH) if h>0 else _BH
        fi,li=s._visible_range()
        vw=s._wm[fi:li];lo=vw[0]if vw else 60;hi=s._wm[li-1]if li>fi else 71
        # ═══ white keys ═══
        lf=QFont("Sans",9)
        for i,midi in enumerate(vw):
            x=i*kw+2;y=2.0;r=QRectF(x,y,kw-2,kh);pc=midi%12
            if midi==s._bass and midi in s._hl:fl=_CHB
            elif midi in s._hl:fl=s._hl[midi]
            elif pc in s._sp:fl=_CHS
            else:fl=_CW
            p.setBrush(QBrush(fl));p.setPen(QPen(_CBD,2.0));p.drawRoundedRect(r,2,2)
            if pc==0:
                lb=f"C{midi//12-1}";p.setFont(lf);p.setPen(QPen(_CT,1))
                fm=QFontMetrics(lf);tw=fm.horizontalAdvance(lb)
                p.drawText(QPointF(x+kw-2-tw-4,y+kh-fm.height()-2+fm.ascent()),lb)
        # ═══ black keys ═══
        for midi in s._bm:
            if midi<lo-1 or midi>hi+1:continue
            lw=midi-1
            if lw not in s._wm:continue
            fwi=s._wm.index(lw);wi=fwi-fi
            if wi<0 or wi>=len(vw)-1:continue
            x=(wi+1)*kw+1-bw/2;y=2.0;r=QRectF(x,y,bw,bh);pc=midi%12
            if midi==s._bass and midi in s._hl:fl=_CHBB
            elif midi in s._hl:fl=_CHCB
            elif pc in s._sp:fl=_CHSB
            else:fl=_CB
            pen=QPen(_CBG,2.0)if midi in s._hl else QPen(QColor(0,0,0,0),0)
            p.setBrush(QBrush(fl));p.setPen(pen);p.drawRoundedRect(r,2,2)
    def mousePressEvent(s,ev):
        midi=s._midi_at(ev.position().x(),ev.position().y())
        if midi is not None:
            if midi in s._hl:del s._hl[midi]
            else:s._hl[midi]=_CHC
            s.update();s.noteClicked.emit(midi,_midi_name(midi))
    def _midi_at(s,mx,my):
        w,h=s.width(),s.height()
        if w<=0 or h<=0:return None
        kw=_WW;kh=float(h-4);bw=_BW;bh=_BH*(h/_TH)if h>0 else _BH
        fi,li=s._visible_range()
        vw=s._wm[fi:li];lo=vw[0]if vw else 60;hi=s._wm[li-1]if li>fi else 71
        for midi in s._bm:
            if midi<lo-1 or midi>hi+1:continue
            lw=midi-1
            if lw not in s._wm:continue
            fwi=s._wm.index(lw);wi=fwi-fi
            if wi<0 or wi>=len(vw)-1:continue
            x=(wi+1)*kw+1-bw/2;y=2.0
            if x<=mx<=x+bw and y<=my<=y+bh:return midi
        for i,midi in enumerate(vw):
            x=i*kw+2;y=2.0
            if x<=mx<=x+kw-2 and y<=my<=y+kh:return midi
        return None

def _midi_name(midi):
    return f"{NOTE_NAMES[midi%12]}{midi//12-1}"

# ── Demo ──────────────────────────────────────────────────────────────────────
_CHORDS={
    "C maj":[60,64,67],"D min":[62,65,69],"F maj":[65,69,72],
    "G7":[67,71,74,77],"Am":[69,72,76],
}
_SCALES={
    "C maj":[60,62,64,65,67,69,71,72],
    "C min":[60,62,63,65,67,68,70,72],
}

class PianoDemo(QWidget):
    def __init__(s):
        super().__init__()
        s.setWindowTitle("Piano Keyboard – PySide6");s.resize(1012,340)
        s.setStyleSheet("background-color:#1a1a2e;")
        l=QVBoxLayout(s);l.setContentsMargins(8,8,8,8);l.setSpacing(8)
        s._lb=QLabel("Ready – 🖱 scroll to pan | click keys to toggle")
        s._lb.setStyleSheet("color:#a0a5c0;font-size:13px;padding:4px 8px;background:#22223a;border-radius:4px;")
        s._lb.setAlignment(Qt.AlignmentFlag.AlignCenter);l.addWidget(s._lb)
        s.pn=PianoWidget()
        s.pn.setStyleSheet("border:1px solid #505060;border-radius:4px;")
        l.addWidget(s.pn,stretch=1)
        s.pn.noteClicked.connect(lambda m,n:print(f"Note: {n} (MIDI={m})"))
        # buttons
        br=QHBoxLayout();br.setSpacing(8)
        bs="QPushButton{background:#2a2a4a;color:#c0c5e0;border:1px solid #505070;border-radius:4px;padding:6px 14px;font-size:12px;}QPushButton:hover{background:#3a3a6a;}QPushButton:pressed{background:#4a4a7a;}"
        for lb,cb in[("C Chord",lambda:s._chord("C maj")),("Dm Chord",lambda:s._chord("D min")),("F Chord",lambda:s._chord("F maj")),("G7",lambda:s._chord("G7")),("Am",lambda:s._chord("Am")),("C Maj Scale",lambda:s._scale("C maj")),("C Min Scale",lambda:s._scale("C min")),("Clear",s._clear)]:
            b=QPushButton(lb);b.setStyleSheet(bs);b.clicked.connect(cb);br.addWidget(b)
        br.addStretch();l.addLayout(br)
        # auto‑demo
        s._ds=[lambda:s._demo("C maj","C maj",60),lambda:s._demo("D min","C maj",62),lambda:s._demo("F maj","C maj",65),lambda:s._demo("G7","C maj",67),lambda:s._demo("Am","C maj",69),lambda:s._demo("C maj","C min",60)]
        s._di=0;s._tm=QTimer(s);s._tm.timeout.connect(s._next);s._tm.start(3000)
        s._ds[0]()
    def _chord(s,n):
        ms=_CHORDS[n];s.pn.clear_all();s.pn.highlight_notes(ms);s.pn.set_bass_note(ms[0])
        s._lb.setText(f"  Chord: {n}  |  bass: {_midi_name(ms[0])}")
    def _scale(s,n):
        ms=_SCALES[n];s.pn.clear_all();s.pn.set_scale_pcs(ms)
        s._lb.setText(f"  Scale: {n}  (no chord, no bass)")
    def _demo(s,cn,sn,bass):
        s.pn.clear_all();s.pn.highlight_notes(_CHORDS[cn])
        s.pn.set_scale_pcs(_SCALES[sn]);s.pn.set_bass_note(bass)
        s._lb.setText(f"  Chord: {cn}  |  Scale: {sn}  |  Bass: {_midi_name(bass)}")
    def _clear(s):
        s.pn.clear_all();s._lb.setText("  Cleared")
    def _next(s):
        s._ds[s._di]();s._di=(s._di+1)%len(s._ds)

def main():
    app=QApplication(sys.argv);app.setStyle("Fusion")
    w=PianoDemo();w.show();sys.exit(app.exec())
if __name__=="__main__":main()

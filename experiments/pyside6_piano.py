"""PySide6 Piano Keyboard Widget — 3 octaves (C4–B6) with click interaction"""
from __future__ import annotations
import sys, typing as t
from PySide6.QtCore import Qt, Signal, QRectF, QSize
from PySide6.QtGui import *
from PySide6.QtWidgets import *

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
_START_MIDI = 60          # C4
_NUM_OCTAVES = 3
_WPC  = {0,2,4,5,7,9,11}
_BPC  = {1,3,6,8,10}
_WHITE_MIDIS = [m for m in range(_START_MIDI,_START_MIDI+_NUM_OCTAVES*12) if m%12 in _WPC]
_BLACK_MIDIS = [m for m in range(_START_MIDI,_START_MIDI+_NUM_OCTAVES*12) if m%12 in _BPC]
_BPC_LIST = [1,3,6,8,10]
_BW_SLOT = {1:0,3:1,6:3,8:4,10:5}
_WW, _WH = 48.0, 160.0
_BW, _BH = 30.0, 100.0
_BXO = [_WW-_BW/2, 2*_WW-_BW/2, 4*_WW-_BW/2, 5*_WW-_BW/2, 6*_WW-_BW/2]
_TW = _NUM_OCTAVES*7*_WW+4; _TH = _WH+4
_CW=QColor(255,255,255);_CB=QColor(24,24,28);_CBD=QColor(40,40,50)
_CHC=QColor(255,210,50);_CHS=QColor(100,180,255);_CHB=QColor(80,230,80)
_CHBL=QColor(200,160,30);_CT=QColor(20,20,30);_CBG=QColor(26,26,46)

class PianoWidget(QWidget):
    noteClicked=Signal(int,str)
    def __init__(s,parent=None):
        super().__init__(parent)
        s.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
        s.setMinimumSize(340,180)
        s._hl={}; s._sp=set()
        s._white_midis=[m for m in range(21,109) if m%12 in _WPC]
        s._black_midis=[m for m in range(21,109) if m%12 in _BPC]
        s._scroll_midi=60
    def highlight_note(s,midi,color=None):
        if color is None:color=_CHC
        s._hl[midi]=color; s.update()
    def highlight_notes(s,midis,color=None):
        if color is None:color=_CHC
        for m in midis:s._hl[m]=color
        s.update()
    def set_scale_pcs(s,midis):
        s._sp=set(midis); s.update()
    def clear_highlights(s):
        s._hl.clear(); s.update()
    def clear_all(s):
        s._hl.clear(); s._sp.clear(); s.update()
    def sizeHint(s):return QSize(52*48+4,180)
    def minimumSizeHint(s):return QSize(340,180)
    def _visible_range(s):
        w=s.width()
        n=max(7,int(w//_WW))
        try:ci=s._white_midis.index(s._scroll_midi)
        except ValueError:ci=0
        fi=ci-n//2;li=fi+n
        t=len(s._white_midis)
        if fi<0:fi=0;li=min(n,t)
        if li>t:li=t;fi=max(0,t-n)
        return fi,li
    def paintEvent(s,ev):
        p=QPainter(s);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=s.width(),s.height()
        if w<=0 or h<=0:return
        kw=_WW;kh=float(h-4);bw=_BW;bh=_BH*(h/_TH) if h>0 else _BH
        fi,li=s._visible_range()
        vw=s._white_midis[fi:li]
        lo=vw[0]if vw else 60;hi=s._white_midis[li-1]if li>fi else 71
        for i,midi in enumerate(vw):
            x=i*kw+2;y=2.0;r=QRectF(x,y,kw-2,kh)
            pc=midi%12
            if midi in s._hl:fl=s._hl[midi]
            elif pc in s._sp:fl=_CHS
            else:fl=_CW
            p.setBrush(QBrush(fl));p.setPen(QPen(_CBD,2.0));p.drawRoundedRect(r,2,2)
        for midi in s._black_midis:
            if midi<lo-1 or midi>hi+1:continue
            left_white=midi-1
            if left_white not in s._white_midis:continue
            full_wi=s._white_midis.index(left_white)
            wi=full_wi-fi
            if wi<0 or wi>=len(vw)-1:continue
            x=(wi+1)*kw+1-bw/2;y=2.0;r=QRectF(x,y,bw,bh)
            pc=midi%12
            if midi in s._hl:fl=s._hl[midi]
            elif pc in s._sp:fl=QColor(40,80,180)
            else:fl=_CB
            pen=QPen(_CBG,2.0)if midi in s._hl else QPen(QColor(0,0,0,0),0)
            p.setBrush(QBrush(fl));p.setPen(pen);p.drawRoundedRect(r,2,2)
    def mousePressEvent(s,ev):
        midi=s._midi_at(ev.position().x(),ev.position().y())
        if midi is not None:
            if midi in s._hl:del s._hl[midi]
            else:s._hl[midi]=_CHC
            s.update()
            s.noteClicked.emit(midi,_midi_name(midi))
    def _midi_at(s,mx,my):
        w,h=s.width(),s.height()
        if w<=0 or h<=0:return None
        kw=_WW;kh=float(h-4);bw=_BW;bh=_BH*(h/_TH)if h>0 else _BH
        fi,li=s._visible_range()
        vw=s._white_midis[fi:li]
        lo=vw[0]if vw else 60;hi=s._white_midis[li-1]if li>fi else 71
        for midi in s._black_midis:
            if midi<lo-1 or midi>hi+1:continue
            left_white=midi-1
            if left_white not in s._white_midis:continue
            full_wi=s._white_midis.index(left_white)
            wi=full_wi-fi
            if wi<0 or wi>=len(vw)-1:continue
            x=(wi+1)*kw+1-bw/2;y=2.0
            if x<=mx<=x+bw and y<=my<=y+bh:return midi
        for i,midi in enumerate(vw):
            x=i*kw+2;y=2.0
            if x<=mx<=x+kw-2 and y<=my<=y+kh:return midi
        return None

def _midi_name(midi):
    return f"{NOTE_NAMES[midi%12]}{midi//12-1}"


class PianoDemo(QWidget):
    def __init__(s):
        super().__init__()
        s.setWindowTitle("Piano Keyboard - PySide6"); s.resize(1012,220)
        l=QVBoxLayout(s); l.setContentsMargins(0,0,0,0)
        s.pn=PianoWidget(); l.addWidget(s.pn)
        s.pn.setStyleSheet("border:1px solid #505060;")
        s.setStyleSheet("background-color:#1a1a2e;")
        s.pn.noteClicked.connect(lambda midi,name:print(f"Note clicked: {name} (MIDI={midi})"))
def main():
    app=QApplication(sys.argv); app.setStyle("Fusion")
    w=PianoDemo(); w.show(); sys.exit(app.exec())
if __name__=="__main__":main()

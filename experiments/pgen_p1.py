"""Generate pyside6_piano.py - part 1: header + PianoWidget body"""
CODE='''"""PySide6 Piano Keyboard Widget - single octave with click interaction"""
from __future__ import annotations
import sys, typing as t
from PySide6.QtCore import Qt, Signal, QRectF, QSize
from PySide6.QtGui import *
from PySide6.QtWidgets import *

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
WHITE_PCS  = [0,2,4,5,7,9,11]
BLACK_PCS  = [1,3,6,8,10]
_WW, _WH = 48.0, 160.0
_BW, _BH = 30.0, 100.0
_BXO = [_WW-_BW/2, 2*_WW-_BW/2, 4*_WW-_BW/2, 5*_WW-_BW/2, 6*_WW-_BW/2]
_TW = 7*_WW+4; _TH = _WH+4
_CW=QColor(255,255,255);_CB=QColor(24,24,28);_CBD=QColor(40,40,50)
_CHC=QColor(255,210,50);_CHS=QColor(100,180,255);_CHB=QColor(80,230,80)
_CHBL=QColor(200,160,30);_CT=QColor(20,20,30)

class PianoWidget(QWidget):
    noteClicked=Signal(int)
    def __init__(s,parent=None):
        super().__init__(parent)
        s.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
        s.setMinimumSize(200,100)
        s._hl={}; s._sp=set()
    def highlight_note(s,pc,color=None):
        if color is None:color=_CHC
        s._hl[pc]=color; s.update()
    def highlight_notes(s,pcs,color=None):
        if color is None:color=_CHC
        for pc in pcs:s._hl[pc]=color
        s.update()
    def set_scale_pcs(s,pcs):
        s._sp=set(pcs); s.update()
    def clear_highlights(s):
        s._hl.clear(); s.update()
    def clear_all(s):
        s._hl.clear(); s._sp.clear(); s.update()
    def sizeHint(s):return QSize(int(_TW),int(_TH))
    def minimumSizeHint(s):return QSize(200,100)
    def paintEvent(s,ev):
        p=QPainter(s);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w,h=s.width(),s.height()
        kw=_WW*(w/_TW);kh=_WH*(h/_TH);bw=_BW*(w/_TW);bh=_BH*(h/_TH)
        for i,pc in enumerate(WHITE_PCS):
            x=i*kw+2;y=2.0;r=QRectF(x,y,kw-2,kh)
            if pc in s._hl:fl=s._hl[pc]
            elif pc in s._sp:fl=_CHS
            else:fl=_CW
            p.setBrush(QBrush(fl));p.setPen(QPen(_CBD,1.0));p.drawRoundedRect(r,2,2)
        for i,pc in enumerate(BLACK_PCS):
            x=_BXO[i]*(kw/_WW)+2-bw/2;y=2.0;r=QRectF(x,y,bw,bh)
            if pc in s._hl:fl=_CHBL
            elif pc in s._sp:fl=QColor(40,80,180)
            else:fl=_CB
            p.setBrush(QBrush(fl));p.setPen(QPen(QColor(0,0,0,0),0));p.drawRoundedRect(r,2,2)
    def mousePressEvent(s,ev):
        pc=s._pc_at(ev.position().x(),ev.position().y())
        if pc is not None:s.noteClicked.emit(pc)
    def _pc_at(s,mx,my):
        w,h=s.width(),s.height()
        kw=_WW*(w/_TW);kh=_WH*(h/_TH);bw=_BW*(w/_TW);bh=_BH*(h/_TH)
        for i,pc in enumerate(BLACK_PCS):
            x=_BXO[i]*(kw/_WW)+2-bw/2;y=2.0
            if x<=mx<=x+bw and y<=my<=y+bh:return pc
        for i,pc in enumerate(WHITE_PCS):
            x=i*kw+2;y=2.0
            if x<=mx<=x+kw-2 and y<=my<=y+kh:return pc
        return None
'''
t=r'C:\Users\devin\Documents\VCWorkspace\KLO_Chords\experiments\pyside6_piano.py'
with open(t,'w',encoding='utf-8') as f:f.write(CODE)
import py_compile
try:
    py_compile.compile(t,doraise=True);print(f'Part 1: {len(CODE)} bytes, SYNTAX OK')
except py_compile.PyCompileError as e:print(f'SYNTAX ERROR: {e}')

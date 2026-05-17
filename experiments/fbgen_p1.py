"""Generate pyside6_fretboard.py - part 1"""
CODE='''"""PySide6 Guitar Fretboard Widget - 6 strings, 12 frets"""
from __future__ import annotations
import sys, typing as t
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import *
from PySide6.QtWidgets import *
SN=["E","A","D","G","B","e"];CH=["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
OP=[4,9,2,7,11,4];FF,LF,NF=0,12,13;DC={5:3,4:2,3:0,2:1,1:0,0:0}
def nn(si,fr):return""if fr<0 else CH[(OP[si]+fr)%12]
class FretboardWidget(QWidget):
    noteClicked=Signal(int,int,int)
    def __init__(s,parent=None):
        super().__init__(parent)
        s.setMinimumSize(400,200);s.setSizePolicy(QSizePolicy.MinimumExpanding,QSizePolicy.MinimumExpanding)
        s.setMouseTracking(True);s.dots=[{}for _ in range(6)];s._ld(DC)
        s._hl={};s._rp=None;s.hs=s.hf=None
        s.bg=QColor("#1e1e2e");s.fc=QColor("#cdd6f4");s.sc=QColor("#585b70");s.nc=QColor("#f5c2e7")
        s.dc_=QColor("#f9e2af");s.db=QColor("#fab387");s.tc=QColor("#cdd6f4");s.hc=QColor("#89b4fa")
        s.nlc=QColor("#1e1e2e");s.oc=QColor("#a6e3a1");s._ml=50;s._mr=20;s._mt=30;s._mb=45
    def gd(s,si,fr):return s.dots[si].get(fr,False)
    def sd(s,si,fr,st):
        if st:s.dots[si][fr]=True
        else:s.dots[si].pop(fr,None)
        s.update()
    def td(s,si,fr):s.sd(si,fr,not s.gd(si,fr))
    def cad(s):s.dots=[{}for _ in range(6)];s.update()
    def _ld(s,ch):
        s.dots=[{}for _ in range(6)]
        for st,fr in ch.items():
            if 0<=st<6 and FF<=fr<=LF:s.dots[st][fr]=True
    def highlight_pc(s,pc,color=None):
        if color is None:color=QColor(255,210,50)
        for st in range(6):
            for fr in range(13):
                if((OP[st]+fr)%12)==pc:s._hl[(st,fr)]=color
        s.update()
    def highlight_notes(s,pcs,color=None):
        if color is None:color=QColor(255,210,50)
        ps=set(pcs)
        for st in range(6):
            for fr in range(13):
                if((OP[st]+fr)%12)in ps:s._hl[(st,fr)]=color
        s.update()
    def clear_highlights(s):s._hl.clear();s.update()
    def set_root_pc(s,pc):s._rp=pc;s.update()
    def clear_all(s):s._hl.clear();s._rp=None;s.update()
    def pc_at(s,st,fr):return(OP[st]+fr)%12
    def _sy(s,si,sp):return s._mt+sp*0.5+si*sp
    def _fx(s,fi,fp):return s._ml+fi*fp
    def _lo(s):
        w,h=s.width(),s.height()
        fp=(w-s._ml-s._mr)/12.0 if w>70 else 20.0
        sp=(h-s._mt-s._mb)/5.0 if h>75 else 20.0
        return sp,fp
'''
t=r'C:\Users\devin\Documents\VCWorkspace\KLO_Chords\experiments\pyside6_fretboard.py'
with open(t,'w',encoding='utf-8') as f:f.write(CODE)
import py_compile
try:
    py_compile.compile(t,doraise=True);print(f'Part 1: {len(CODE)} bytes, SYNTAX OK')
except py_compile.PyCompileError as e:print(f'SYNTAX ERROR: {e}')

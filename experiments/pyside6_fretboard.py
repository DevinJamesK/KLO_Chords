"""PySide6 Guitar Fretboard Widget - 6 strings, 12 frets"""
from __future__ import annotations
import sys, typing as t
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import *


from PySide6.QtWidgets import *
SN=["E","A","D","G","B","e"];CH=["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
OP=[4,9,2,7,11,4];FF,LF,NF=0,12,13;DC={5:3,4:2,3:0,2:1,1:0,0:0}
CHROMATIC = CH
OPEN_PITCHES = OP
STRING_NAMES = SN

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

    def paintEvent(s,ev):
        p=QPainter(s)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(s.rect(),s.bg);ss,fs=s._lo();fbh=s.height()-s._mt-s._mb
        nlw=max(2,min(8,fs*.07));flw=max(.6,min(3,fs*.025));slw=max(.5,min(3,fs*.02));nfs=max(7,min(16,int(fs*.18)));snfs=max(8,min(18,int(ss*.45)));tnfs=max(5,min(14,int(min(ss,fs)*.32)));dr=max(4,min(16,int(min(ss,fs)*.32)));fmr=max(3,min(8,fs*.09));fmo=ss*.5
        for fr in range(NF):
            x=s._fx(fr,fs);y0,y1=s._mt,s._mt+fbh
            p.setPen(QPen(s.nc if fr==0 else s.fc,nlw if fr==0 else flw))
            p.drawLine(int(x),int(y0),int(x),int(y1))
        p.setPen(QPen(s.sc,slw))
        for st in range(6):
            y=s._sy(st,ss);p.drawLine(int(s._ml),int(y),int(s._fx(LF,fs)),int(y))
        p.setFont(QFont("Consolas",nfs));p.setPen(s.tc)
        for fr in range(NF):p.drawText(QPointF(int(s._fx(fr,fs))-int(nfs*.8),s.height()-s._mb+int(nfs*2)),str(fr))
        p.setFont(QFont("Consolas",snfs,QFont.Weight.Bold));p.setPen(s.tc)
        for st in range(6):p.drawText(QPointF(8,int(s._sy(st,ss))+int(snfs*.35)),SN[st])
        p.setBrush(QBrush(QColor(140,135,100)));p.setPen(QPen(QColor(0,0,0,0),0))
        cy=(s._mt+s.height()-s._mb)/2
        for fr in(3,5,7,9):p.drawEllipse(QPointF(s._fx(fr,fs)+fs/2,cy),fmr,fmr)
        mx12=s._fx(12,fs)+fs/2;p.drawEllipse(QPointF(mx12,cy-fmo),fmr,fmr);p.drawEllipse(QPointF(mx12,cy+fmo),fmr,fmr)
        p.setFont(QFont("Consolas",tnfs,QFont.Weight.Bold))
        for st in range(6):
            for fr in range(FF,LF+1):
                if not s.gd(st,fr):continue
                x=s._fx(fr,fs)+fs/2;y=s._sy(st,ss);npc=(OP[st]+fr)%12;k=(st,fr)
                ih=k in s._hl;ir=s._rp is not None and npc==s._rp
                if fr==0:
                    r=min(ss,fs)*0.30;p.setPen(QPen(s.oc,max(1.5,min(4,fs*.03))));p.setBrush(Qt.NoBrush)
                    p.drawEllipse(QPointF(x,y),r,r);nm=nn(st,fr);p.setPen(s.tc)
                    fm=QFontMetrics(p.font());p.drawText(QPointF(int(x)-fm.horizontalAdvance(nm)/2,int(y)+int(tnfs*.5)),nm)
                else:
                    if ih:dc=s._hl[k]
                    elif ir:dc=QColor(60,210,100)
                    else:dc=s.dc_
                    p.setBrush(QBrush(dc));p.setPen(QPen(QColor(0,0,0,0),0))
                    p.drawEllipse(QPointF(x,int(y)),dr,dr)
                    p.setPen(QColor(20,20,30));nm=CH[npc];fm=QFontMetrics(p.font());p.drawText(QPointF(int(x)-fm.horizontalAdvance(nm)/2,int(y)+int(tnfs*.35)),nm)
        if s.hs is not None and s.hf is not None:
            cx=s._fx(s.hf,fs);cy=s._sy(s.hs,ss);r=min(ss,fs)*0.38
            p.setPen(QPen(s.hc,max(1.5,min(4,fs*.03))));p.setBrush(Qt.NoBrush);p.drawEllipse(QPointF(cx,cy),r,r)
        p.end()
    def _ht(s,pos):
        ss,fs=s._lo();mg=max(4,min(12,fs*.12))
        x=pos.x();fr=round((x-s._ml)/fs)if fs>0 else 0
        fr=max(FF,min(LF,fr))
        if abs(x-s._fx(fr,fs))>fs*0.45+mg:fr=None
        y=pos.y();st=round((y-s._mt)/ss)if ss>0 else 0
        st=max(0,min(5,st))
        if abs(y-s._sy(st,ss))>ss*0.45+mg:st=None
        return st,fr
    def mousePressEvent(s,ev):
        if ev.button()==Qt.LeftButton:
            st,fr=s._ht(ev.position())
            if st is not None and fr is not None:
                s.td(st,fr);s.noteClicked.emit(st,fr,s.pc_at(st,fr))
    def mouseMoveEvent(s,ev):
        s.hs,s.hf=s._ht(ev.position());s.update()
    def leaveEvent(s,ev):s.hs=s.hf=None;s.update()

class FretboardDemo(QWidget):
    def __init__(s):
        super().__init__();s.setWindowTitle("Guitar Fretboard - PySide6");s.resize(900,320)
        l=QVBoxLayout(s);l.setContentsMargins(0,0,0,0);s.fb=FretboardWidget();l.addWidget(s.fb,1)
        b=QHBoxLayout();b.setContentsMargins(10,0,10,6)
        s.info=QLabel("Click any fret to toggle dot | C Major pre-loaded")
        s.info.setStyleSheet("color:#a6adc8;font-family:Consolas;font-size:11px;");b.addWidget(s.info)
        s.cnt=QLabel("Dots: 5");s.cnt.setStyleSheet("color:#f9e2af;font-family:Consolas;font-size:11px;")
        b.addWidget(s.cnt);l.addLayout(b);s.fb.update.connect(s._upd)
        s.setStyleSheet("background-color:#1e1e2e;")
    def _upd(s):s.cnt.setText(f"Dots: {sum(1 for sd in s.fb.dots for _ in sd.values())}")

def main():
    app=QApplication(sys.argv);app.setStyle("Fusion")
    p=app.palette();p.setColor(p.ColorRole.Window,QColor("#1e1e2e"))
    p.setColor(p.ColorRole.WindowText,QColor("#cdd6f4"));app.setPalette(p)
    w=FretboardDemo();w.show();sys.exit(app.exec())
if __name__=="__main__":main()


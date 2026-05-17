"""Generate pyside6_fretboard.py - part 2"""
CODE='''
    def paintEvent(s,ev):
        p=QPainter(s)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(s.rect(),s.bg);ss,fs=s._lo();fbh=s.height()-s._mt-s._mb
        for fr in range(NF):
            x=s._fx(fr,fs);y0,y1=s._mt,s._mt+fbh
            p.setPen(QPen(s.nc if fr==0 else s.fc,4 if fr==0 else 1.5))
            p.drawLine(int(x),int(y0),int(x),int(y1))
        p.setPen(QPen(s.sc,1.2))
        for st in range(6):
            y=s._sy(st,ss);p.drawLine(int(s._ml),int(y),int(s._fx(LF,fs)),int(y))
        p.setFont(QFont("Consolas",10));p.setPen(s.tc)
        for fr in range(NF):p.drawText(QPointF(int(s._fx(fr,fs))-8,s.height()-s._mb+20),str(fr))
        p.setFont(QFont("Consolas",11,QFont.Weight.Bold));p.setPen(s.tc)
        for st in range(6):p.drawText(QPointF(8,int(s._sy(st,ss))+4),SN[st])
        p.setBrush(QBrush(QColor(140,135,100)));p.setPen(QPen(QColor(0,0,0,0),0))
        cy=(s._mt+s.height()-s._mb)/2
        for fr in(3,5,7,9):p.drawEllipse(QPointF(s._fx(fr,fs)+fs/2,cy),5,5)
        mx12=s._fx(12,fs)+fs/2;p.drawEllipse(QPointF(mx12,cy-12),5,5);p.drawEllipse(QPointF(mx12,cy+12),5,5)
        p.setFont(QFont("Consolas",8,QFont.Weight.Bold))
        for st in range(6):
            for fr in range(FF,LF+1):
                if not s.gd(st,fr):continue
                x=s._fx(fr,fs)+fs/2;y=s._sy(st,ss);npc=(OP[st]+fr)%12;k=(st,fr)
                ih=k in s._hl;ir=s._rp is not None and npc==s._rp
                if fr==0:
                    r=min(ss,fs)*0.30;p.setPen(QPen(s.oc,2));p.setBrush(Qt.NoBrush)
                    p.drawEllipse(QPointF(x,y),r,r);nm=nn(st,fr);p.setPen(s.tc)
                    fm=QFontMetrics(p.font());p.drawText(QPointF(int(x)-fm.horizontalAdvance(nm)/2,int(y)+4),nm)
                else:
                    if ih:dc=s._hl[k]
                    elif ir:dc=QColor(60,210,100)
                    else:dc=s.dc_
                    p.setBrush(QBrush(dc));p.setPen(QPen(QColor(0,0,0,0),0))
                    p.drawEllipse(QPointF(x,int(y)),8,8)
                    p.setPen(QColor(20,20,30));p.drawText(QPointF(int(x)-7,int(y)+3),CH[npc])
        if s.hs is not None and s.hf is not None:
            cx=s._fx(s.hf,fs);cy=s._sy(s.hs,ss);r=min(ss,fs)*0.38
            p.setPen(QPen(s.hc,2));p.setBrush(Qt.NoBrush);p.drawEllipse(QPointF(cx,cy),r,r)
        p.end()
    def _ht(s,pos):
        ss,fs=s._lo();mg=6.0
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
'''
t=r'C:\Users\devin\Documents\VCWorkspace\KLO_Chords\experiments\pyside6_fretboard.py'
with open(t,'a',encoding='utf-8') as f:f.write(CODE)
import py_compile
try:
    py_compile.compile(t,doraise=True);print(f'Part 2: {len(CODE)} bytes, SYNTAX OK')
except py_compile.PyCompileError as e:print(f'SYNTAX ERROR: {e}')

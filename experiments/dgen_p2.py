"""Generate pyside6_demo.py - part 2 (append CombinedDemo + main)"""
CODE='''

class CombinedDemo(QMainWindow):
    def __init__(s):
        super().__init__()
        s.setWindowTitle("KLO Chords - PySide6 Prototype")
        s.setMinimumSize(900,500); s.resize(1100,600)
        c=QWidget(); s.setCentralWidget(c)
        ml=QVBoxLayout(c); ml.setSpacing(8); ml.setContentsMargins(10,10,10,10)

        tb=QHBoxLayout()
        tb.addWidget(QLabel("Key:"))
        s.kc=QComboBox(); s.kc.addItems(KEY_NAMES); s.kc.setCurrentText("C")
        s.kc.currentTextChanged.connect(s._upd)
        tb.addWidget(s.kc); tb.addSpacing(16)

        tb.addWidget(QLabel("Scale:"))
        s.sc=QComboBox(); s.sc.addItems(list(SCALE_INTERVALS.keys())); s.sc.setCurrentText("Major")
        s.sc.currentTextChanged.connect(s._upd)
        tb.addWidget(s.sc); tb.addSpacing(24)

        tb.addWidget(QLabel("Scale notes:"))
        s.snl=QLabel("C  D  E  F  G  A  B")
        s.snl.setStyleSheet("font-family:Consolas;font-size:14px;font-weight:bold;color:#e0e0e0;padding:4px 8px;background-color:#2a2a3a;border-radius:4px;")
        tb.addWidget(s.snl,1)
        ml.addLayout(tb)

        sep=QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setFrameShadow(QFrame.Shadow.Sunken); sep.setStyleSheet("color:#444;")
        ml.addWidget(sep)

        bl=QHBoxLayout()
        fc=QWidget(); fc.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        fl=QVBoxLayout(fc); fl.setContentsMargins(0,0,0,0)
        fl.addWidget(QLabel("Guitar Fretboard")); fl.itemAt(0).widget().setStyleSheet("font-weight:bold;color:#aaa;background:transparent;")
        s.fb=FretboardWidget(); s.fb.setMinimumSize(300,160); fl.addWidget(s.fb,1)
        bl.addWidget(fc,3)

        pc_=QWidget(); pc_.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        pl=QVBoxLayout(pc_); pl.setContentsMargins(0,0,0,0)
        pl.addWidget(QLabel("Piano Keyboard")); pl.itemAt(0).widget().setStyleSheet("font-weight:bold;color:#aaa;background:transparent;")
        s.pn=PianoWidget(); s.pn.setMinimumSize(200,100); pl.addWidget(s.pn,1)
        bl.addWidget(pc_,2)
        ml.addLayout(bl,1)

        s.pn.noteClicked.connect(s._pc)
        s.fb.noteClicked.connect(s._fc)

        s.setStyleSheet("QMainWindow{background-color:#1a1a2e}QWidget{background-color:#1a1a2e;color:#cdd6f4}QLabel{background:transparent}QComboBox{background-color:#2a2a3e;color:#cdd6f4;border:1px solid #444;border-radius:4px;padding:4px 8px;min-width:80px}QComboBox::drop-down{border:none}QComboBox QAbstractItemView{background-color:#2a2a3e;color:#cdd6f4;selection-background-color:#3a3a5e}QFrame{background-color:#444}")
        s._upd()

    def _upd(s):
        key=s.kc.currentText(); sc=s.sc.currentText()
        notes=get_scale_notes(key,sc)
        s.snl.setText("  ".join(notes))
        root_pc=KEY_NAMES.index(key)
        intervals=SCALE_INTERVALS.get(sc,SCALE_INTERVALS["Major"])
        scale_pcs={(root_pc+i)%12 for i in intervals}
        s.pn.set_scale_pcs(scale_pcs)
        s.fb.set_root_pc(root_pc)
        s.pn.clear_highlights(); s.fb.clear_highlights()

    def _pc(s,pc):
        s.fb.clear_highlights(); s.fb.highlight_pc(pc)
        s.pn.clear_highlights(); s.pn.highlight_note(pc)

    def _fc(s,si,fr,pc):
        s.pn.clear_highlights(); s.pn.highlight_note(pc)
        s.fb.clear_highlights(); s.fb.highlight_pc(pc)

def main():
    app=QApplication(sys.argv); app.setStyle("Fusion")
    p=app.palette(); p.setColor(p.ColorRole.Window,QColor("#1a1a2e"))
    p.setColor(p.ColorRole.WindowText,QColor("#cdd6f4"))
    p.setColor(p.ColorRole.Base,QColor("#2a2a3e"))
    p.setColor(p.ColorRole.Text,QColor("#cdd6f4")); app.setPalette(p)
    w=CombinedDemo(); w.show(); sys.exit(app.exec())

if __name__=="__main__": main()
'''
t=r'C:\Users\devin\Documents\VCWorkspace\KLO_Chords\experiments\pyside6_demo.py'
with open(t,'a',encoding='utf-8') as f:f.write(CODE)
import py_compile
try:
    py_compile.compile(t,doraise=True)
    print(f'Part 2: appended {len(CODE)} bytes, SYNTAX OK')
except py_compile.PyCompileError as e:
    print(f'SYNTAX ERROR: {e}')

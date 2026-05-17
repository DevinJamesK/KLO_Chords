"""Generate pyside6_piano.py - part 2 (append main/demo)"""
CODE='''

class PianoDemo(QWidget):
    def __init__(s):
        super().__init__()
        s.setWindowTitle("Piano Keyboard - PySide6"); s.resize(400,200)
        l=QVBoxLayout(s); l.setContentsMargins(0,0,0,0)
        s.pn=PianoWidget(); l.addWidget(s.pn)
        s.setStyleSheet("background-color:#1a1a2e;")
        s.pn.noteClicked.connect(lambda pc:print(f"Note clicked: PC={pc}"))
def main():
    app=QApplication(sys.argv); app.setStyle("Fusion")
    w=PianoDemo(); w.show(); sys.exit(app.exec())
if __name__=="__main__":main()
'''
t=r'C:\Users\devin\Documents\VCWorkspace\KLO_Chords\experiments\pyside6_piano.py'
with open(t,'a',encoding='utf-8') as f:f.write(CODE)
import py_compile
try:
    py_compile.compile(t,doraise=True);print(f'Part 2: appended {len(CODE)} bytes, SYNTAX OK')
except py_compile.PyCompileError as e:print(f'SYNTAX ERROR: {e}')

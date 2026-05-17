"""Generate pyside6_demo.py - part 1"""
CODE='''
"""
KLO Chords - PySide6 Prototype
Combined demo: piano keyboard + guitar fretboard side-by-side.
"""
from __future__ import annotations
import sys, typing as t
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QFrame, QSizePolicy,
)
sys.path.insert(0, __import__("os").path.dirname(__file__) or ".")
from pyside6_piano import PianoWidget, NOTE_NAMES, WHITE_PCS, BLACK_PCS
from pyside6_fretboard import FretboardWidget, CHROMATIC, OPEN_PITCHES

SCALE_INTERVALS = {
    "Major":[0,2,4,5,7,9,11],"Minor":[0,2,3,5,7,8,10],
    "Harmonic Minor":[0,2,3,5,7,8,11],"Melodic Minor":[0,2,3,5,7,9,11],
    "Pentatonic Maj":[0,2,4,7,9],"Pentatonic Min":[0,3,5,7,10],
    "Blues":[0,3,5,6,7,10],"Dorian":[0,2,3,5,7,9,10],
    "Phrygian":[0,1,3,5,7,8,10],"Lydian":[0,2,4,6,7,9,11],
    "Mixolydian":[0,2,4,5,7,9,10],"Locrian":[0,1,3,5,6,8,10],
}
KEY_NAMES = ['C','Db','D','Eb','E','F','F#','G','Ab','A','Bb','B']

def get_scale_notes(root_name, scale_name):
    root_pc = KEY_NAMES.index(root_name)
    intervals = SCALE_INTERVALS.get(scale_name, SCALE_INTERVALS["Major"])
    pcs = [(root_pc + i) % 12 for i in intervals]
    use_sharp = "#" in root_name
    result = []
    for pc in pcs:
        n = CHROMATIC[pc]
        if not use_sharp and "#" in n:
            n = {"C#":"Db","D#":"Eb","F#":"Gb","G#":"Ab","A#":"Bb"}.get(n, n)
        result.append(n)
    return result
'''
t=r'C:\Users\devin\Documents\VCWorkspace\KLO_Chords\experiments\pyside6_demo.py'
with open(t,'w',encoding='utf-8') as f:f.write(CODE)
print(f'Part 1: {len(CODE)} bytes to {t}')

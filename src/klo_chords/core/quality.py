"""
Chord quality formatting.
Short symbols for compact display, full names for the detail panel.
"""


def quality_symbol(quality: str) -> str:
    """Short chord quality suffix, e.g. 'min', 'min7', 'maj7', '°'."""
    return {
        "M": "", "m": "min", "dim": "°", "aug": "+",
        "7": "7", "m7": "min7", "maj7": "maj7", "dim7": "°7",
        "m7b5": "min7b5", "mmaj7": "minMaj7", "aug7": "+7", "augmaj7": "+Maj7",
        "sus2": "sus2", "sus4": "sus4",
    }.get(quality, quality)


def quality_spelled(quality: str) -> str:
    """Full quality name for the detail panel, e.g. 'minor', 'minor 7'."""
    return {
        "M": "Major", "m": "minor", "dim": "Diminished", "aug": "Augmented",
        "7": "7", "m7": "minor 7", "maj7": "major 7", "dim7": "diminished 7",
        "m7b5": "minor 7b5", "mmaj7": "minor major 7", "aug7": "augmented 7", "augmaj7": "augmented major 7",
        "sus2": "sus2", "sus4": "sus4",
    }.get(quality, quality)

"""
Analyze chords with semantic labels based on pitch-class pattern matching.

Functions:
- chord_quality
"""

###############################################################################
# Built-in Imports
from collections.abc import Iterable
# Local Imports
from pyramidi.analysis.forte import get_pc

__all__ = ["chord_quality"]

###############################################################################
# Constants
CHORD_QUALITIES = {
    "maj": {0, 4, 7},
    "min": {0, 3, 7},
    "dim": {0, 3, 6},
    "aug": {0, 4, 8},
    "sus2": {0, 2, 7},
    "sus4": {0, 5, 7},
    "dom7": {0, 4, 7, 10},
    "maj7": {0, 4, 7, 11},
    "min7": {0, 3, 7, 10},
    "half-dim7": {0, 3, 6, 10},
    "dim7": {0, 3, 6, 9},
}

###############################################################################
def chord_quality(chord: Iterable[int]) -> str | None:
    """Identify the quality of a chord by matching the intervals to a dictionary.

    Arguments:
    chord (Iterable[int]) -- MIDI numbers or pitch classes.

    Returns:
    tuple[int, str] -- Pitch class of identified root, and a chord quality.

    """
    pcs = get_pc(chord)

    if len(pcs) < 3:
        return None  # Not a chord.

    for root in pcs:
        normalized = {(pc - root) % 12 for pc in pcs}

        for quality, template in CHORD_QUALITIES.items():
            if normalized == template:
                return root, quality

    return None

###############################################################################

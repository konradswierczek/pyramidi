"""
Analyze chords based on Allen Forte's set theory.

Functions:
- get_pc
- get_intervals
- interval_vector
- bass_intervals
"""

###############################################################################
# Built-in Imports
from collections.abc import Iterable
from itertools import combinations

__all__ = ["get_pc", "get_intervals", "interval_vector", "bass_intervals"]

###############################################################################
def get_pc(chord: Iterable[int]) -> set[int]:
    """Get unique pitch classes.

    Arguments:
    chord (Iterable[int]) -- MIDI numbers or pitch classes.

    Returns:
    set -- Unique pitch classes.
    
    """
    return {note % 12 for note in chord}

###############################################################################
def get_intervals(chord: Iterable[int]) -> list[int]:
    """All interval classes of a chord

    Arguments:
    chord (Iterable[int]) -- MIDI numbers or pitch classes.

    Returns:
    list -- interval classes.
    """
    # Get all intervals
    pcs = sorted(get_pc(chord))
    return [abs(a - b) for a, b in combinations(pcs, 2)]

###############################################################################
def interval_vector(chord: Iterable[int]) -> list[int]:
    """Interval Vector of a chord after Forte 1973.

    Arguments:
    chord (Iterable[int]) -- MIDI numbers or pitch classes.

    Returns:
    list -- interval vector.

    """
    iv = [0] * 6
    for interval in get_intervals(chord):
        ic = min(interval, 12 - interval)
        if ic != 0:
            iv[ic - 1] += 1
    return iv

###############################################################################
def bass_intervals(chord: Iterable[int]) -> list[int]:
    """Semitone distances between lowest note in a chord.
    
    Arguments:
    chord (Iterable[int]) -- MIDI numbers or pitch classes.

    Returns:
    tuple -- interval classes from bass note

    """
    pitches = sorted(chord)
    bass = pitches[0]
    return tuple(
        (p - bass) % 12
        for p in pitches[1:]
        if (p - bass) % 12 != 0
    )

###############################################################################

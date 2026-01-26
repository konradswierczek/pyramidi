"""
MIDI-based Score Defined Cues used in the Emotional Piano Project at the MAPLE Lab, McMaster University.

Functons:
- get_attacks
- get_arScore
- get_mmWt
- get_pitchHeight

TODO: Measure-wise sdc.
"""

###############################################################################
# Third Party Imports
from mido import tick2second
# Local Imports
from pyramidi.abstract import Slice, Bite

__all__ = ["attacks", "arScore", "pitchHeight"]

###############################################################################
def attacks(slices: list[Slice]) -> int:
    """Count the number of attacks.

    Arguments:
    slices (list[Slice]) -- A list of Slice objects returned by slice_salami.

    Returns:
    int -- The number of attacks

    """
    return len(slices)

###############################################################################
def arScore(slices: list[Slice]) -> float:
    """Calculate the attacks per second based on MIDI tempo.

    Arguments:
    slices (list[Slice]) -- A list of Slice objects returned by slice_salami.

    Returns:
    float -- The number of attacks per second based on the MIDI tempo.
    # TODO: This assumes the tempo at the end is a global tempo.

    """
    return len(slices) / tick2second(
        sum([i.duration for i in slices]),
        slices[-1].ticks_per_beat,
        slices[-1].tempo
    )

###############################################################################
def pitchHeight(slices: list[Slice]):
    """Calculate the weighted keyboard number pitch height.

    Arguments:
    slices (list[Slice]) -- A list of Slice objects returned by slice_salami.

    Returns:
    float -- Weighted average pitch height

    """
    total_weight = 0.0
    weighted_sum = 0.0
    for ev in slices:
        dur = ev.duration_seconds
        keynums = ev.keynum

        for k in keynums:
            weighted_sum += k * dur
            total_weight += dur

    return weighted_sum / total_weight

###############################################################################

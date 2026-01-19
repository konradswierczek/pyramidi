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
        slices[-1].end,
        slices[-1].ticks_per_beat,
        slices[-1].tempo
    )

###############################################################################
def pitchHeight(bites: list[Bite]):
    """Calculate the weighted keyboard number pitch height.

    Arguments:
    slices (list[Bite]) -- A list of Slice objects returned by slice_bites.

    Returns:
    float -- Weighted average pitch height

    """
    full_duration = sum([i.duration_seconds for i in bites])
    pitch_height = sum(
        [i.keynum * i.duration_seconds for i in bites]
    ) / full_duration
    return pitch_height

###############################################################################

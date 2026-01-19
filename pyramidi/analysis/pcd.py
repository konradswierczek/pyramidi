"""
Pitch Class Distribution from mido.MidiFile (abstracted by slice_bites) with customizable weights.

Functions:
- pcd
- weight_count
- weight_tick
- weight_durationalaccent
- weight_timedvelocity
"""
# Third Party Imports
from numpy import exp
from mido import tick2second
# Local Imports
from pyramidi.abstract import Bite

__all__ = ["pcd", "weight_count", "weight_tick", "weight_durationalaccent", "weight_timedvelocity"]

###############################################################################
def pcd(
    bites: list[Bite],
    weight_function = None,
    normalize = False
) -> dict:
    """Compute a pitch-class distribution with customizable weights.

    Arguments:
    slices (list[Bite]) -- A list of Slice objects returned by slice_bites.
    weight_function (function) -- callable or None to apply weights to pcd.
        Function (note, dur_ticks, midi) -> weight.
        If None, raw duration in ticks is used.
    normalize (bool) -- If True, normalize to sum of pitch classes to 1. Default is False.
        
    Returns:
    dictionary -- Pitch-class distribution {0..11: value}
    """
    pcd = dict.fromkeys(range(12), 0.0)

    for bite in bites:
        weight = weight_function(bite) if weight_function else bite.duration
        pcd[bite.pc] += weight

    if normalize:
        total = sum(pcd.values()) or 1.0
        pcd = {k: v / total for k, v in pcd.items()}

    return pcd

###############################################################################
def weight_count(bite: Bite) -> float:
    """Weigh a note by the fact that it was played: each note counts no matter how long.
    TO BE USED WITH `pcd` FUNCTION

    Arguments:
    bite (Bite) -- Bite dataclass

    Returns:
    float -- weighting to be applied for pitch class distribution

    """
    return 1.0

###############################################################################
def weight_tick(bite: Bite) -> float:
    """Weigh a note by its duration in ticks.
    TO BE USED WITH `pcd` FUNCTION

    Arguments:
    bite (Bite) -- Bite dataclass

    Returns:
    float -- weighting to be applied for pitch class distribution

    """
    return bite.duration

###############################################################################
def weight_durationalaccent(bite: Bite, tau = 0.5, accent_index = 2) -> float:
    """Weigh a note using Parncutt's (1994) durational accent model as implemented in MIDItoolbox.
    TO BE USED WITH `pcd` FUNCTION

    Arguments:
    bite (Bite) -- Bite dataclass

    Returns:
    float -- weighting to be applied for pitch class distribution

    """
    return float((1.0 - exp(-bite.duration_seconds / tau)) ** accent_index)

###############################################################################
def weight_timedvelocity(bite: Bite) -> float:
    """Weigh a note based on both its duration in ticks and velocity.
    TO BE USED WITH `pcd` FUNCTION

    Arguments:
    bite (Bite) -- Bite dataclass

    Returns:
    float -- weighting to be applied for pitch class distribution

    """
    v = bite.velocity / 127.0
    return bite.duration * v

###############################################################################

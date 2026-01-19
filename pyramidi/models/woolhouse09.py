"""
Interval Cycle Proximity Tonal Attraction Algorithm after Woolhouse 2009.
Implemented by Konrad Swierczek, Karen Chan, & Matthew Woolhouse. 
Digital Music Lab, McMaster University

functions:
- event_attraction
- chroma_attraction
"""

###############################################################################
# Built-in Imports
from itertools import combinations
from math import gcd
# Third Party Imports
from numpy import array
# Local Imports
from pyramidi.models.parncutt88 import pitch_salience

__all__ = [
    'event_attraction',
    'chroma_attraction'
]
###############################################################################
# Constants

CONSONANT_INTERVALS = {0, 3, 4, 5, 7, 8, 9, 12}
ALLPC = list(range(0, 12))

# Diatonic Sets, represented by pitch class root (0 = C) and mode (ma = major).
# Values are represented in pitch classes.

# TODO: Fix these for proper convention, probably generate like in krumhansl90.
DIATONIC_SETS = {
    '0ma': [0,2,4,5,7,9,11],
    '1ma': [1,3,5,6,8,10,0],
    '2ma': [2,4,6,7,9,11,1],
    '3ma': [3,5,7,8,10,0,2],
    '4ma': [4,6,8,9,11,1,3],
    '5ma': [5,7,9,10,0,2,4],
    '6ma': [6,8,10,11,1,3,5],
    '7ma': [7,9,11,0,2,4,6],
    '8ma': [8,10,0,1,3,5,7],
    '9ma': [9,11,1,2,4,6,8],
    '10ma': [10,0,2,3,5,7,9],
    '11ma': [11,1,3,4,6,8,10]
}
SCALES = {
    'ka0ma': [0,2,4,5,7,9,11],
    'ka1ma': [1,3,5,6,8,10,0],
    'ka2ma': [2,4,6,7,9,11,1],
    'ka3ma': [3,5,7,8,10,0,2],
    'ka4ma': [4,6,8,9,11,1,3],
    'ka5ma': [5,7,9,10,0,2,4],
    'ka6ma': [6,8,10,11,1,3,5],
    'ka7ma': [7,9,11,0,2,4,6],
    'ka8ma': [8,10,0,1,3,5,7],
    'ka9ma': [9,11,1,2,4,6,8],
    'ka10ma': [10,0,2,3,5,7,9],
    'ka11ma': [11,1,3,4,6,8,10]
}

###############################################################################
def event_attraction(
    pre_chord: list[int],
    suc_chord: list[int],
    alpha: float = 99999,
    beta: float = 4,
    gamma: float = 8,
    delta: float = 0.1
) -> float:
    """Pairwise Tonal Attraction after Woolhouse 2009.

    Arguments:
    pre_chord (list[int]) -- preceding chord.
    succ chord (list[int]) -- succeding chord.
    alpha (float) -- Voice Leading weighting variable.
    beta (float) -- Preceding chord Root Salience weighting variable.
    gamma (float) -- Succeding chord Root Salience weighting variable.
    delta (float) -- Consonance/Dissonance weighting variable.

    Returns:
    float -- Tonal attraction of preceding chord to succeeding chord.
    """

    ###########################################################################
    def cd_chord(chord: list[int]) -> bool:
        """Calculate if chord contains consonant or dissonant intervals."""
        pcs = [note % 12 for note in chord]
        intervals = [abs(a - b) for a, b in combinations(pcs, 2)]
        return any(interval in CONSONANT_INTERVALS for interval in intervals)

    ###########################################################################
    def pd(midi_1: int, midi_2: int) -> int:
        """Calculate semitone distance between two midi numbers."""
        return abs(midi_1 - midi_2)

    ###########################################################################
    def ic(pd: int) -> int:
        """Calculate interval cycle of given interval."""
        return int(12 / (gcd(int(pd), 12)))

    ###########################################################################
    # Pitch Distance Matrix
    pdlist = [[pd(pre_note, suc_note) for suc_note in suc_chord] for pre_note in pre_chord]

    # Interval Cycle Matrix
    iclist = [[ic(cell) for cell in row] for row in pdlist]
    ic_mat = array(iclist).reshape(len(pre_chord), len(suc_chord))

    # Voice Leading Matrix
    vllist = [[None if pd is None else (alpha / (pd + alpha)) for pd in row] for row in pdlist]
    vl_mat = array(vllist).reshape(len(pre_chord), len(suc_chord))

    # Interval Cycle/Voice Leading Matrix
    icvl = ic_mat * vl_mat

    # Root Salience 1 Matrix (placeholder)
    rs1list= [[1 if vl > 0 else 0 for vl in row] for row in vllist]
    rs1 = array(rs1list).reshape(len(pre_chord),len(suc_chord))

    # Calculate root of chords using Parncutt 1993
    prec_root = pitch_salience(pre_chord)["root"]
    succ_root = pitch_salience(suc_chord)["root"]

    rs_prec = []
    for note in pre_chord:
        if note == prec_root:
            rs_prec.append(beta)
        else:
            rs_prec.append(1)
    rs_succ = []
    for note in suc_chord:
        if note == succ_root:
            rs_succ.append(gamma)
        else:
            rs_succ.append(1)
    rs2list = [[pre_note * suc_note for suc_note in rs_succ] for pre_note in rs_prec]
    rs2_sum = sum([sum(rs2) for rs2 in rs2list])
    rs2_matrix = array(rs2list).reshape(len(pre_chord), len(suc_chord))

    # Root Salience 3 Matrix
    rs3 = array([num / rs2_sum for cell in rs2_matrix for num in cell]).reshape(len(pre_chord), len(suc_chord))

    # Consonance/Dissonance Matrix
    prec_cd = cd_chord(pre_chord)
    succ_cd = cd_chord(suc_chord)
    if prec_cd == succ_cd:
        cd = rs3
    elif prec_cd and not succ_cd:
        cd = (1 + delta) * rs3
    elif not prec_cd and succ_cd:
        cd = (1 - delta) * rs3

    # Calculate Event Attraction
    ea_matrix = icvl * cd
    ea = sum(sum(ea_matrix)) / 12
    return ea

###############################################################################
def chroma_attraction(
    chord: list[int],
    beta: float = 4
) -> dict[int, float]:
    """Calculate the tonal attraction of a chord to every chroma.

    Arguments:
    chord (list[int]) -- MIDI numbers or pitch classes of a chord.
    beta (float) -- Chord Root Salience weighting variable.

    Returns:
    dict[int, float] -- keys = chroma, values = tonal attraction of chord to chroma.

    """
    return {
        pc: float(
            event_attraction(
                chord,
                [pc],
                alpha = 9999,
                beta = beta,
                gamma = 1,
                delta = 0
            )
        ) for pc in ALLPC
    }

###############################################################################
# TODO: FIX EVERYTHING BELOW ME.
def key_attraction(chord):
    """
    """
    ca = chroma_attraction(chord)
    ka = {}
    for name, scale in SCALES.items():
        ka_list = []
        for pc in SCALES[name]:
            ka_list.append(ca[pc])
            ka[name] = sum(ka_list)/ len(ka_list)
    return ka

###############################################################################
def diatonicity(
    chord,
    epsilon = 1
):
    """
    This function identifies the diatonic relation 
    of inputted chords to DIATONIC_SETS
    chord = midi
        epsilon = 
    """
    cardinality = len(chord)
    unique_pc = list(set([note % 12 for note in chord]))
    counts = [(len(set(unique_pc).intersection(DIATONIC_SETS[scale]))) \
              for scale in DIATONIC_SETS]
    diatonic_weight = [round((scale_count + epsilon) / (7 + epsilon) *
                             (scale_count + epsilon) / 
                             (cardinality + epsilon),3) \
                       for scale_count in counts]
    diatonicity = {}
    for scale, weight in zip(DIATONIC_SETS.keys(), diatonic_weight):
        diatonicity.update({scale: weight})
    return diatonicity

###############################################################################

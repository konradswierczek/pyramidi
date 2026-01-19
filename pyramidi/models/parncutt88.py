"""
Pitch Salience Algorithm based on Parncutt 1988,1993
Implemented by Konrad Swierczek and Karen Chan in 2022
Digital Music Lab, McMaster University

functions:
- pitch_salience
"""

###############################################################################
# Built-in Imports
from collections.abc import Iterable

__all__ = ["pitch_salience"]

###############################################################################
# Constants
WEIGHTS88 = [1, 0, 0.2, 0.1, 0.33, 0, 0, 0.5, 0, 0, 0.25, 0]
WEIGHTS93 = [10, 0, 1, 0, 3, 0, 0, 5, 0, 0, 2, 0]

###############################################################################
def pitch_salience(chord: Iterable[int], weights = 93):
    """Calculate pitch salience after Parncutt (1988; 1993)

    Arguments:
    chord (Iterable[int]) -- MIDI numbers or pitch classes.
    weights (int) -- 88 or 93 after Parncutt's two different weight options.

    Returns:
    dict -- Pitch-salience analysis results with keys:
    'pitch_salience' (list[float]) : normalized salience values for pitch classes 0–11.
    'root_pc' (int | None) : estimated root pitch class, or None if ambiguous.
    'ra' (float) : root ambiguity.

    """
    pcs = set(note % 12 for note in chord)
    pc_vector = [1 if i in pcs else 0 for i in range(12)]

    w = WEIGHTS88 if weights == 88 else WEIGHTS93

    weight_sums = []
    for root in range(12):
        indices = [(root + i) % 12 for i in range(len(w))]
        weight_sums.append(
            sum(pc_vector[i] * w[j] for j, i in enumerate(indices))
        )

    max_sum = max(weight_sums)
    rasums = [v / max_sum for v in weight_sums]
    ra = round(sum(rasums) ** 0.5, 3)
    ps = [round((1 / ra) * v, 3) for v in rasums]

    maxima = [i for i, v in enumerate(ps) if v == max(ps)]

    root_pc = maxima[0] if len(maxima) == 1 else None

    return {
        "pitch_salience": ps,
        "root_pc": root_pc,
        "ra": ra
    }

###############################################################################

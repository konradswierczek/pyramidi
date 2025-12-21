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
# Built-in Imports
from statistics import mean
# Third Party Imports
from mido import second2tick, MidiFile
# Local Imports
from pyramidi.core import midi2keyboard, slice_salami, get_notes

###############################################################################
def get_attacks(midi: MidiFile):
    """Count the number of attacks.

    Arguments:
    midi (MidiFile) -- A mido MidiFile

    Returns:
    int -- The number of attacks

    """
    return len(slice_salami(midi))

###############################################################################
def get_arScore(midi: MidiFile):
    """Calculate the attacks per second based on MIDI tempo.

    Arguments:
    midi (MidiFile) -- A mido MidiFile

    Returns:
    float -- The number of attacks per second.
    
    """
    attacks = get_attacks(midi)
    return attacks / midi.length

###############################################################################
def get_pitchHeight(midi: MidiFile):
    """Calculate the weighted keyboard number pitch height.

    Arguments:
    midi (MidiFile) -- A mido MidiFile

    Returns:
    float -- Weighted average pitch height

    """
    notes = get_notes(midi)
    tpb = midi.ticks_per_beat
    full_duration = sum([i[1] / tpb for i in notes])
    pitch_height = sum([midi2keyboard(i[0]) * (i[1] / tpb) for i in notes]) / full_duration
    return pitch_height

###############################################################################

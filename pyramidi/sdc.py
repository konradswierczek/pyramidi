"""
"""
###############################################################################
# Local Imports
from pyramidi.analysis import salami
from pyramidi.core import midi2keyboard
# Third Party Imports
from mido import second2tick
###############################################################################
def get_pitchHeight(midi):
    """
    """
    # Create lists to store pitch and timing information.
    pitch = []
    weight = []
    for t in range(len(midi.tracks)):
        # Loop across all messages, including an index number.
        for i, msg in enumerate(midi.tracks[t]):
            # Find "note_off" to go with a given "note_on".
            if msg.type == "note_on":
                # For each new message, restart the next message overall timing counter.
                next_abs_time = 0
                for next in range(i + 1, len(midi.tracks[t])):
                    next_msg = midi.tracks[t][next]
                    next_abs_time = next_abs_time + next_msg.time
                    if next_msg.type == "note_off" and \
                    next_msg.note == msg.note: 
                        pitch.append(midi2keyboard(msg.note))
                        weight.append(next_abs_time / midi.ticks_per_beat)
                        break
    return sum([p * w for (p, w) in zip(pitch, weight)]) / sum(weight)

###############################################################################
# NOT TESTED IN BETA
def beat_density(midi_file: str = 'tests/test.mid'):
    midi = midi_file
    ticks = int(second2tick(midi.length, midi.ticks_per_beat, get_tempo(midi)))
    beats = int(ticks / midi.ticks_per_beat)
    slices = salami(midi)
    return len(slices) / beats

###############################################################################
# NOT TESTED IN BETA
def onset_rate(midiFile, time_unit: str = "beat", direct: bool = False):
    """
    """
    if not direct:
        midi = MidiFile(midiFile)
    else:
        midi = midiFile
    tpb = midi.ticks_per_beat
    tempo = [msg.tempo for msg in midi if msg.type == "set_tempo"][0]
    length = int(second2tick(midi.length, tpb, tempo))
    onsets = len(salami(midiFile, direct = direct))
    if time_unit == "beat":
        time_unit = length / tpb
    elif time_unit == "length":
        time_unit = midi.length
    else:
        print("error")
    return onsets / time_unit

###############################################################################
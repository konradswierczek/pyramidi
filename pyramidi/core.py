"""
"""
###############################################################################
# Local Imports
# Third Party Imports
from mido import MidiFile, MidiTrack, MetaMessage, Message, tempo2bpm, merge_tracks
###############################################################################
# Constants
__all__ = ['pre_process', "cut"]
###############################################################################
def pre_process(
    midi_file,
    savepath: str = None
):
    """
    Reformat and preprocess a MIDI file for analysis.
    Returns a Type 0 Mido MidiFile class object.

    Keyword arguments:
    midiFile -- Any '.mid' file with relative path. 
    savepath -- Filepath for a file version of output.
    """
    # TODO: Add savepath functionality
    ###########################################################################
    # Read midi file with Mido.
    midi_data = MidiFile(midi_file)
    # Create new Type 0 Mido MidiFile class object, add input 'ticks_per_beat'.
    new_midi = MidiFile(
        type = 0,
        ticks_per_beat = midi_data.ticks_per_beat
    )
    new_midi.tracks.append(merge_tracks(midi_data.tracks))
    # Return entire Mido MidiFile class object.
    return new_midi

###############################################################################
def lenBar(time_signature: tuple):
    """Given a time signature, returns the number of quarter notes per bar."""
    quarter_notes = (time_signature[0]/time_signature[1]) * 4
    return quarter_notes

###############################################################################
def midi_2_key(midiNumber: int):
    """ Returns piano key number given a MIDI number.
    """
    # Subtract 20 from midiNumber.
    return midiNumber - 20

###############################################################################
def get_tempo(midi_file):
    tempo = [msg.tempo for msg in midi_file if msg.type == "set_tempo"]
    time_sig = [(msg.numerator, msg.denominator) for msg in midi_file if msg.type == "time_signature"]
    tempo2bpm(tempo[0])
    return tempo[0]

###############################################################################
def get_timesig(midi_file):
    time_sig = [(msg.numerator, msg.denominator) for msg in midi_file if msg.type == "time_signature"]
    return time_sig[0]

# =========================================================================== #
def cut(midi_data, measures = 8):
    # variables
    tpb = midi_data.ticks_per_beat
    ticks = int()
    target_ticks = int(
        [lenBar(
            (msg.numerator,
             msg.denominator
            )
        ) * measures * tpb for msg in midi_data.tracks[0] if msg.type == "time_signature"
        ][0])
    active_notes = dict()
    # New midi data
    new = MidiFile(type=0, ticks_per_beat=tpb)
    track = MidiTrack()
    new.tracks.append(track)
    for msg in midi_data.tracks[0]:
        if isinstance(msg, MetaMessage):
            if msg.type == "time_signature":
                time_signature = (msg.numerator, msg.denominator)
                target_ticks = lenBar(time_signature) * measures * tpb
        elif isinstance(msg, Message):
            if msg.type == "note_on" and msg.velocity > 0:
                active_notes[msg.note] = msg.velocity
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                active_notes.pop(msg.note, None)
        ticks += msg.time
        # write
        if ticks > target_ticks:
            break
        elif ticks == target_ticks and  msg.type == "note_on" and msg.velocity > 0:
            break
        else:
            track.append(msg)
    # Clean up
    for leftover in active_notes:
        track.append(Message(type = "note_off", note = leftover, velocity = active_notes[leftover], time = 0))
    track.append(MetaMessage(type = 'end_of_track', time = 1))
    return new

# =========================================================================== #
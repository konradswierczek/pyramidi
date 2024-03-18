"""
"""
###############################################################################
# Local Imports
# Third Party Imports
from mido import MidiFile, MidiTrack, MetaMessage, Message, tempo2bpm
###############################################################################
# Constants
__all__ = ['pre_process']
###############################################################################
def pre_process(midiFile, savepath: str = None):
    """Reformat and preprocess a MIDI file for analysis.
    Returns a Type 0 Mido MidiFile class object.

    Keyword arguments:
    midiFile -- Any '.mid' file with relative path. 
    savepath -- Filepath for a file version of output.
    """
    # TODO: Add savepath functionality
    ###########################################################################
    # Read midi file with Mido.
    midiFile = MidiFile(midiFile)
    # Create new Type 0 Mido MidiFile class object, add input 'ticks_per_beat'.
    new = MidiFile(type = 0, ticks_per_beat = midiFile.ticks_per_beat)
    track = MidiTrack()
    new.tracks.append(track)
    # Loop through tracks in midi file.
    for i in range(len(midiFile.tracks)):
            # Loop through messages in a given track.
            for msg in midiFile.tracks[i]:
                # Filter unneeded messages.
                # NOTE: 'end_of_track' is filtered due to copies exisiting in
                #        the case of multiple tracks.
                if msg.type in ['end_of_track', 'control_change',
                                'program_change']:
                    continue
                # Convert 0 velocity "note_on" to "note_off" messages.
                # NOTE: According to MIDI standard, "note_on" messages with
                #       a velocity of zero are equivilant to "note_off".
                elif msg.type == "note_on" and msg.velocity == 0:
                    track.append(Message('note_off', 
                                         note = msg.note,
                                         velocity = msg.velocity,
                                         time = msg.time))
                # Copy all other messages directly.
                else:
                    track.append(msg.copy())
    # Add 'end_of_track' message.
    track.append(MetaMessage(type = 'end_of_track', time = 1))
    # Return entire Mido MidiFile class object.
    return new

###############################################################################
def lenBar(timeSignature: tuple):
    """Given a time signature, returns the number of quarter notes per bar."""
    # Divide 4 by denominator of time signature for standard beat unit.
    beat_unit = 4 / timeSignature[1]
    # return numerator of time signature multiplied by standard beat unit.
    return int(timeSignature[0] * beat_unit)

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

###############################################################################
def cut(midiFile, measures: float = 8, direct: bool = False):
    counter = 0
    ongoing_notes = set()
    beats_per_bar = lenBar(get_timesig(midiFile))
    new = MidiFile(type = 0, ticks_per_beat = midiFile.ticks_per_beat)
    track = MidiTrack()
    new.tracks.append(track)
    for i, msg in enumerate(midiFile.tracks[0]):
    # TOP LEVEL: IS THE COUNTER OVER?
        if counter < measures:      
            abs_time = sum(msg.time for msg in track)
    # SECOND LEVEL: IS THE MESSAGE A TIME SIGNATURE?
            if msg.type == "time_signature":
                    time_sig = (msg.numerator, msg.denominator)
                    beats_per_bar = lenBar(time_sig)
            elif msg.type == 'note_on' and msg.velocity > 0:
                ongoing_notes.add(msg.note)
            elif msg.type == 'note_off' or msg.type == "note_on" and msg.velocity == 0:
                ongoing_notes.discard(msg.note)
            track.append(msg)
            counter = (msg.time/midiFile.ticks_per_beat)/beats_per_bar + counter
        elif counter >= measures:
            break
    for open_note in ongoing_notes:
        track.append(Message(type = 'note_off', note = open_note, time = 0))
    track.append(MetaMessage(type = 'end_of_track', time = 1))
    return new

###############################################################################
"""
"""
###############################################################################
# Local Imports
# Third Party Imports
from mido import (
    MidiFile, MidiTrack, tempo2bpm
)

# =========================================================================== #
def get_timeSignature(mid):
    """
    Look for the first time_signature meta event in any track.
    If more than one distinct time signature is found, print a warning and return the first.
    If none is found, default to 4/4.
    """
    found = []
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'time_signature':
                ts = (msg.numerator, msg.denominator)
                if ts not in found:
                    found.append(ts)
    if found:
        if len(found) > 1:
            print(f"\033[31mWarning: Multiple distinct time signatures found. Using the first one: \033[35m{found[0]}\033[0m")
        return found[0]
    return (4, 4)

# =========================================================================== #
def get_measureLength(mid, time_signature):
    """
    Given a mido MidiFile and a time signature (numerator, denominator),
    compute the number of ticks in one full measure.
    
    Formula:
       measure_ticks = ticks_per_beat * numerator * (4 / denominator)
    """
    numerator, denominator = time_signature
    ticks_per_beat = mid.ticks_per_beat
    measure_ticks = ticks_per_beat * numerator * (4 / denominator)
    return int(measure_ticks)

# =========================================================================== #
def get_totalTicks(mid):
    """
    Given a mido.MidiFile object, compute the total absolute time in ticks.
    This function calculates the cumulative time for each track (by summing 
    delta times) and returns the maximum value encountered, which represents 
    the total duration of the file.
    
    Parameters:
        mid (mido.MidiFile): The MIDI file loaded using mido.

    Returns:
        int: The total absolute time in ticks.
    """
    total_time = 0
    for track in mid.tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
        total_time = max(total_time, abs_time)
    return total_time

# =========================================================================== #
def cut_midi(mid, length_in_ticks):
    """
    Cuts a MidiFile to a specified length (in ticks).
    
    Parameters:
        mid (mido.MidiFile): The original MIDI file.
        length_in_ticks (int): The desired length of the new MIDI file in ticks.
        
    Returns:
        mido.MidiFile: The cut MIDI file.
    """
    # Merge all tracks into one list of events with absolute time.
    events = []
    for track in mid.tracks:
        abs_time = 0
        for msg in track:
            abs_time += msg.time
            events.append((abs_time, msg))
    
    # Filter events that happen before the given length in ticks.
    events_to_keep = [
        (abs_time, msg) for abs_time, msg in events if abs_time < length_in_ticks
    ]
    
    # Rebuild a single track from the filtered events
    new_track = MidiTrack()
    last_time = 0
    for abs_time, msg in sorted(events_to_keep, key = lambda x: x[0]):
        delta = abs_time - last_time
        new_msg = msg.copy(time = delta)
        new_track.append(new_msg)
        last_time = abs_time
    
    # Create a new MidiFile object and add the new track
    new_mid = MidiFile(ticks_per_beat = mid.ticks_per_beat)
    new_mid.tracks.append(new_track)
    
    return new_mid

# =========================================================================== #
def midi2keyboard(midi_number: int):
    """ Returns piano key number given a MIDI number.
    """
    return midi_number - 20

###############################################################################
def get_tempo(midi_file):
    tempo = [msg.tempo for msg in midi_file if msg.type == "set_tempo"]
    time_sig = [(msg.numerator, msg.denominator) for msg in midi_file if msg.type == "time_signature"]
    tempo2bpm(tempo[0])
    return tempo[0]

###############################################################################
"""
"""
###############################################################################
# Local Imports
from warnings import warn
# Third Party Imports
from mido import (
    MidiFile, MidiTrack, tempo2bpm, merge_tracks, MetaMessage, Message
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

###############################################################################
def get_tempo(midi_file):
    tempo = [msg.tempo for msg in midi_file if msg.type == "set_tempo"]
    time_sig = [(msg.numerator, msg.denominator) for msg in midi_file if msg.type == "time_signature"]
    tempo2bpm(tempo[0])
    return tempo[0]

# =========================================================================== #
def get_ticks_mm(midi: MidiFile, n_measures: int = 8) -> int:
    """
    Walk through the single track of a type‑0 file until `n_measures` have elapsed,
    then return the total number of ticks.
    Assumes an initial time signature of 4/4 if none is encountered immediately.
    """
    tpb = midi.ticks_per_beat

    # Default time‑signature = 4/4
    numerator, denominator = 4, 4
    ticks_per_measure = numerator * (4 / denominator) * tpb

    total_ticks = 0
    measure_ticks = 0
    measures_counted = 0

    # Only one track in type 0
    track = midi.tracks[0]

    for msg in track:

        # Add measure for anacrusis
        if msg.type == "program_change" and msg.time > 0:
            n_measures += 1

        # Handle time‑signature changes
        if msg.type == "time_signature":
            numerator, denominator = msg.numerator, msg.denominator
            ticks_per_measure = numerator * (4 / denominator) * tpb
            measure_ticks = 0  # reset into the new signature

        # Advance time
        total_ticks += msg.time
        measure_ticks += msg.time

        # Count off full measures (catches any overshoot)
        while measure_ticks >= ticks_per_measure:
            measures_counted += 1
            measure_ticks -= ticks_per_measure

            if measures_counted >= n_measures:
                return total_ticks

    return total_ticks

# =========================================================================== #
def pre_process(midi: MidiFile) -> MidiFile:
    """
    Convert any MidiFile (type 0, 1, or 2) into a type 0 MidiFile by merging all tracks.

    Parameters
    ----------
    mid : MidiFile
        The source MIDI file (can be type 0, 1, or 2).

    Returns
    -------
    MidiFile
        A new MidiFile of type 0, with one track containing all merged events.
    """
    # Create a new MidiFile with type 0 and same timing resolution
    new_mid = MidiFile(type = 0, ticks_per_beat = midi.ticks_per_beat)

    # Merge all existing tracks into a single track
    merged = merge_tracks(midi.tracks)

    # Create a new track and copy merged events into it
    new_mid.tracks.append(merged)

    return new_mid
    
# =========================================================================== #
def filter_msgs(mid: MidiFile, types_to_filter):
    """
    Return a Type 0 MidiFile with all messages whose .type is in `types_to_filter` removed.

    Parameters
    ----------
    mid : MidiFile
        The source MIDI file (should be Type 0).
    types_to_filter : str or tuple or list of str
        Message type name(s) to filter out, e.g. 'note_on', ('note_off', 'note_on').
        
    Returns
    -------, MidiTrack, merge_tracks
    MidiFile
        A new MidiFile of type 0, with one track containing the filtered events.
    """
    # Normalize filter list
    if isinstance(types_to_filter, str):
        types = (types_to_filter,)
    elif isinstance(types_to_filter, (list, tuple)):
        types = tuple(types_to_filter)
    else:
        raise TypeError(f"types_to_filter must be str, list or tuple, got {type(types_to_filter)}")

    # Build new Type 0 file
    filtered = MidiFile(type=0, ticks_per_beat=mid.ticks_per_beat)
    track0 = MidiTrack()
    for msg in mid.tracks[0]:
        # preserve timing (msg.time is delta)
        if msg.type not in types:
            track0.append(msg)
    filtered.tracks.append(track0)

    return filtered

# =========================================================================== #
def cut_midi(mid: MidiFile, cut_tick: int) -> MidiFile:
    """
    Return a new MidiFile (Type 0) containing only events strictly before `cut_tick`.
    Ensures all notes active at `cut_tick` are turned off at that point, and adds a single End-of-Track.
    """
    new_mid = MidiFile(type=0)
    new_mid.ticks_per_beat = mid.ticks_per_beat

    track = MidiTrack()
    new_mid.tracks.append(track)

    cum_tick = 0
    active_notes = {}  # (channel, note) -> count

    for msg in mid.tracks[0]:
        next_tick = cum_tick + msg.time

        # copy only messages strictly before the cut
        if next_tick < cut_tick:
            copy = msg.copy()
            track.append(copy)
            cum_tick = next_tick
            # track note state
            if not msg.is_meta and msg.type == 'note_on' and msg.velocity > 0:
                key = (msg.channel, msg.note)
                active_notes[key] = active_notes.get(key, 0) + 1
            elif not msg.is_meta and (msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0)):
                key = (msg.channel, msg.note)
                if key in active_notes:
                    active_notes[key] -= 1
                    if active_notes[key] <= 0:
                        del active_notes[key]
            continue

        # any event at or beyond cut_tick truncates here
        delta = cut_tick - cum_tick
        # if the original event was a note_on, send its off counterpart at cut
        if not msg.is_meta and msg.type == 'note_on' and msg.velocity > 0:
            track.append(Message(
                'note_off', note=msg.note, velocity=0,
                channel=msg.channel, time=delta
            ))
        else:
            # absorb any leftover time into a no-op meta to align the cut
            track.append(MetaMessage('track_name', name='', time=delta))
        cum_tick = cut_tick
        break

    # shut off any notes still active at the cut
    for (chan, note) in list(active_notes.keys()):
        track.append(Message('note_off', note=note, velocity=0, channel=chan, time=0))
    active_notes.clear()

    # add single End-of-Track
    track.append(MetaMessage('end_of_track', time=0))
    return new_mid

# =========================================================================== #
def find_msgType(mid: MidiFile, msg_type: str, min_time: int = 0):
    matches = []
    for track_index, track in enumerate(mid.tracks):
        for msg_index, msg in enumerate(track):
            if msg.type == msg_type and msg.time > min_time:
                matches.append((track_index, msg_index, msg))
    return matches

###############################################################################
def midi2keyboard(midi_number: int):
    """ Returns piano key number given a MIDI number.
    """
    return midi_number - 20

###############################################################################

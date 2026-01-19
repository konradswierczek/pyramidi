"""
Modify mido.MidiFile objects for further use in the package. All entities in this module take mido.MidiFile as their input.

Functions:
- collapse_tracks
- cut_midi
- filter_msgs
- remove_msgs
- get_total_ticks
- get_measure_length
- get_ticks_mm
"""

# =========================================================================== #
# Third Party Imports
from mido import MidiFile, merge_tracks, Message, MetaMessage, MidiTrack

# Functions imported from *.
__all__ = [
    "collapse_tracks", "cut_midi", "get_total_ticks",
    "get_measure_length", "get_ticks_mm"
]

# =========================================================================== #
def collapse_tracks(midi: MidiFile) -> MidiFile:
    """Convert a MidiFile to a type 0 MidiFile
    Arguments:
    midi (MidiFile) -- A mido MidiFile.

    Returns:
    MidiFile -- A new MidiFile of type 0, with one track containing all merged events.
    """
    # Create a new MidiFile with type 0 and same timing resolution.
    new_midi = MidiFile(type = 0, ticks_per_beat = midi.ticks_per_beat)

    # Merge all existing tracks into a single track.
    new_track = merge_tracks(midi.tracks)

    # Create a new track and copy merged events into it.
    new_midi.tracks.append(new_track)

    return new_midi

# =========================================================================== #
def cut_midi(midi: MidiFile, cut_tick: int) -> MidiFile:
    """Cut a MidiFile to specified tick length.

    Arguments:
    midi (MidiFile) -- A mido MidiFile
    cut_tick (int) -- Absolute tick boundary to cut file off at. Use  get_ticks_mm to calculate. 

    Returs:
    MidiFile -- a new MidiFile (Type 0) containing only events strictly before `cut_tick: all notes active at `cut_tick` are turned off at that point, adding a single End-of-Track message.
    TODO: Does this require a type 0 MidiFile?
    """
    new_midi = MidiFile(type=0)
    new_midi.ticks_per_beat = midi.ticks_per_beat

    track = MidiTrack()
    new_midi.tracks.append(track)

    cum_tick = 0 # Total absolute tick counter.
    active_notes = {}  # (channel, note) -> count

    for msg in midi.tracks[0]:
        next_tick = cum_tick + msg.time

        # Copy only messages strictly before the cut.
        if next_tick < cut_tick:
            copy = msg.copy()
            track.append(copy)
            cum_tick = next_tick
            # Track note state.
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

        # Any event at or beyond cut_tick truncates here.
        delta = cut_tick - cum_tick
        # If the original event was a note_on, send its off counterpart at cut.
        if not msg.is_meta and msg.type == 'note_on' and msg.velocity > 0:
            track.append(Message(
                'note_off', note=msg.note, velocity=0,
                channel=msg.channel, time=delta
            ))
        else:
            # Absorb any leftover time into a no-op meta to align the cut.
            track.append(MetaMessage('track_name', name = '', time = delta))
        cum_tick = cut_tick
        break

    # Shut off any notes still active at the cut.
    for (chan, note) in list(active_notes.keys()):
        track.append(Message('note_off', note = note, velocity = 0, channel = chan, time = 0))
    active_notes.clear()

    # Add an end of track message before returning.
    track.append(MetaMessage('end_of_track', time = 0))
    return new_midi

# =========================================================================== #
def filter_msgs(midi: MidiFile, msg_type: str, min_time: int = 0) -> list:
    """Filter messages by type.

    Arguments:
    midi (MidiFile) -- A mido MidiFile
    msg_type (str) -- A midi message type (note_on, note_off, etc.)
    min_time(int) -- Minimum amount of ticks for time parameter (defaults to 0, which includes all messages)  

    Returns:
    list -- All messages of msg_type

    Not currently used internally.
    TODO: msg_type can be a list.
    """
    matches = []
    # Search through all tracks.
    for track_index, track in enumerate(midi.tracks):
        for msg_index, msg in enumerate(track):
            # Return messages that meet the criteria.
            if msg.type == msg_type and msg.time > min_time:
                matches.append((track_index, msg_index, msg))
    return matches

###############################################################################
def remove_msgs(midi: MidiFile, types_to_filter) -> MidiFile:
    """Remove messages of a type.

    Arguments:
    midi (MidiFile) -- The source MidiFIle (should be Type 0).
    types_to_filter -- str or tuple or list of str, message type name(s) to filter out, e.g. 'note_on', ('note_off', 'note_on').
        
    Returns
    MidiFile -- a filtered mido MidiFile
    """
    # Normalize filter list
    if isinstance(types_to_filter, str):
        types = (types_to_filter,)
    elif isinstance(types_to_filter, (list, tuple)):
        types = tuple(types_to_filter)
    else:
        raise TypeError(f"types_to_filter must be str, list or tuple, got {type(types_to_filter)}")

    # Build new Type 0 file
    filtered = MidiFile(type=0, ticks_per_beat=midi.ticks_per_beat)
    track0 = MidiTrack()
    for msg in midi.tracks[0]:
        # preserve timing (msg.time is delta)
        if msg.type not in types:
            track0.append(msg)
    filtered.tracks.append(track0)

    return filtered

# =========================================================================== #
def get_total_ticks(midi: MidiFile) -> int:
    """Count the number of ticks in a MidiFile.
    
    Arguments:
    mid (MidiFile) -- a mido MidiFile.

    Returns:
    int -- The total number of ticks in the MidiFile.
    """
    return max(
        sum(msg.time for msg in track)
        for track in midi.tracks
    )

# =========================================================================== #
def get_measure_length(ticks_per_beat: int, time_signature: tuple[int, int]) -> int:
    """Compute the number of ticks in a theoretical measure.

    Arguments:
    ticks_per_beat (int) --  Ticks per beat in the specified midi context.
    time_signature(tuple) -- A time signature (numerator, denominator), both integers

    Returns:
    int -- The number of ticks in one measure
    """
    numerator, denominator = time_signature
    return int(ticks_per_beat * numerator * (4 / denominator))

# =========================================================================== #
def get_ticks_mm(midi: MidiFile, n_measures: int = 8) -> int:
    """Get the tick legnth of n measures.

    Arguments:
    midi (MidiFile) -- A type 0 mido MidiFile to count.
    n_measures (int) -- The number of measures to count to.

    Returns:
    int -- Number of ticks to the desired n_measures.

    Assumes an initial time signature of 4/4 if none is encountered immediately.
    TODO: Make work with fractions of measures?
    TODO: Make including anacrusis a CHOICE, not mandatory.
    """
    tpb = midi.ticks_per_beat
    track = midi.tracks[0]

    # Default time signature
    time_signature = (4, 4)
    ticks_per_measure = get_measure_length(tpb, time_signature)

    total_ticks = 0
    ticks_into_measure = 0
    measures_counted = 0

    for msg in track:

        # Count pickup as a full measure.
        if msg.type == "program_change" and msg.time > 0:
            n_measures += 1

        # Update meter.
        if msg.type == "time_signature":
            time_signature = (msg.numerator, msg.denominator)
            ticks_per_measure = get_measure_length(tpb, time_signature)
            ticks_into_measure = 0

        # Advance time.
        total_ticks += msg.time
        ticks_into_measure += msg.time

        # Count completed measures (handles overshoot).
        while ticks_into_measure >= ticks_per_measure:
            measures_counted += 1
            ticks_into_measure -= ticks_per_measure

            if measures_counted >= n_measures:
                return total_ticks

    return total_ticks

###############################################################################

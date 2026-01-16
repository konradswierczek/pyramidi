"""
General utilities for working with mido MidiFile objects.

Functions
- get_timeSignature
- get_measureLength
- get_totalTicks
- get_tempo
- get_ticks_mm
- collapse_tracks
- filter_msgs
- cut_midi
- find_msgType
- midi2keyboard
"""

###############################################################################
# Built-in Imports
from warnings import warn
from collections import defaultdict
# Third Party Imports
from mido import (
    MidiFile, MidiTrack, tempo2bpm, merge_tracks, MetaMessage, Message
)

# =========================================================================== #
def get_timeSignature(midi: MidiFile):
    """Return the first time_signature meta message.

    Arguments:
    midi (MidiFile) -- a mido MidiFile

    Returns:
    tuple -- A time signature (first value numerator, second value denominator, both integers)

    If more than one distinct time signature is found, prints a warning and returns the first. If no time signatures are found, returns 4/4.
    Previously used for file cutting, no longer needed internally.
    """
    found = []
    # Check all tracks.
    for track in midi.tracks:
        for msg in track:
            if msg.type == 'time_signature':
                ts = (msg.numerator, msg.denominator)
                # Only append if time signature is unique.
                if ts not in found:
                    found.append(ts)
    if found:
        if len(found) > 1:
            print(
                "\033[31m" + \
                "Warning: Multiple distinct time signatures found. Using the first one: " + \
                "\033[35m" + \
                f"{found[0]}" + \
                "\033[0m"
            )
        return found[0]
    return (4, 4)

# =========================================================================== #
def get_measureLength(midi: MidiFile, time_signature: tuple):
    """Compute the number of ticks in one full measure.

    Arguments:
    midi (MidiFile) --  A mido MidiFile
    time_signature(tuple) -- A time signature (numerator, denominator), both integers

    Returns:
    int -- The number of ticks in one measure
    """
    numerator, denominator = time_signature
    ticks_per_beat = midi.ticks_per_beat
    measure_ticks = ticks_per_beat * numerator * (4 / denominator)
    return int(measure_ticks)

# =========================================================================== #
def get_totalTicks(midi: MidiFile):
    """Count the number of ticks in a MidiFile.
    
    Arguments:
    mid (MidiFile) -- a mido MidiFile

    Returns:
    int -- The total number of ticks in the MidiFile.
    """
    total_time = 0
    for track in midi.tracks:
        abs_time = 0
        for msg in track:
            # Sum of all message delta time.
            abs_time += msg.time
        total_time = max(total_time, abs_time)
    return total_time

###############################################################################
def get_tempo(midi_file):
    """Get the first tempo in a MidiFile, in BPM.

    Arguments:
    midi (MidiFIle) -- A mido MidiFile

    Returns:
    float -- A tempo in bpm

    Doesn't seem very useful anymore...
    """
    tempo = [msg.tempo for msg in midi_file if msg.type == "set_tempo"]
    time_sig = [(msg.numerator, msg.denominator) for msg in midi_file if msg.type == "time_signature"]
    # Return the first tempo event.
    tempo2bpm(tempo[0])
    return tempo[0]

# =========================================================================== #
def get_ticks_mm(midi: MidiFile, n_measures: int = 8) -> int:
    """Get the tick legnth of n measures.

    Arguments:
    midi (MidiFile) -- A mido MidiFile
    n_measures (int) -- The number of measures to count to.

    Returns:
    int -- Number of ticks

    Assumes an initial time signature of 4/4 if none is encountered immediately.
    TODO: Make work with fractions of measures?
    """
    tpb = midi.ticks_per_beat

    # Default time‑signature = 4/4.
    numerator, denominator = 4, 4
    ticks_per_measure = numerator * (4 / denominator) * tpb

    total_ticks = 0
    measure_ticks = 0
    measures_counted = 0

    # Only one track in type 0.
    track = midi.tracks[0]

    for msg in track:

        # Add measure for anacrusis.
        if msg.type == "program_change" and msg.time > 0:
            n_measures += 1

        # Handle time‑signature changes.
        if msg.type == "time_signature":
            numerator, denominator = msg.numerator, msg.denominator
            ticks_per_measure = numerator * (4 / denominator) * tpb
            measure_ticks = 0  # reset into the new signature.

        # Advance time.
        total_ticks += msg.time
        measure_ticks += msg.time

        # Count off full measures (catches any overshoot).
        while measure_ticks >= ticks_per_measure:
            measures_counted += 1
            measure_ticks -= ticks_per_measure

            if measures_counted >= n_measures:
                return total_ticks

    return total_ticks

# =========================================================================== #
def collapse_tracks(midi: MidiFile) -> MidiFile:
    """Convert a MidiFile to type 0 MidiFile
    Arguments:
    midi (MidiFile) -- A mido MidiFile.

    Returns:
    MidiFile -- A new MidiFile of type 0, with one track containing all merged events.
    """
    # Create a new MidiFile with type 0 and same timing resolution
    new_midi = MidiFile(type = 0, ticks_per_beat = midi.ticks_per_beat)

    # Merge all existing tracks into a single track
    new_track = merge_tracks(midi.tracks)

    # Create a new track and copy merged events into it
    new_midi.tracks.append(new_track)

    return new_midi
    
# =========================================================================== #
def filter_msgs(midi: MidiFile, types_to_filter):
    """Remove messages of a type.

    Arguments:
    midi (MidiFile) -- a mido MidiFile
        The source MIDI file (should be Type 0).
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
    """Cut a MidiFile to specified tick length.

    Arguments:
    midi (MidiFile) -- A mido MidiFile
    cut_tick (int) -- Absolute tick boundary to cut file off at. Use  get_ticks_mm to calculate. 

    Return a new MidiFile (Type 0) containing only events strictly before `cut_tick: all notes active at `cut_tick` are turned off at that point, adding a single End-of-Track message.
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

    track.append(MetaMessage('end_of_track', time = 0))
    return new_midi

# =========================================================================== #
def find_msgType(midi: MidiFile, msg_type: str, min_time: int = 0):
    """Filter messages by type.

    Arguments:
    midi (MidiFile): A mido MidiFile
    msg_type (str): A midi message type (note_on, note_off, etc.)
    min_time(int): Minimum amount of ticks for time parameter (defaults to 0, which includes all messages)  

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
def midi2keyboard(midi_number: int):
    """Convert MIDI number to keyboard number

    Arguments:
    midi_number (int) -- Any MIDI number between 0 and 127

    Returns:
    integer -- Corresponding keyboard number (-20 MIDI)
    """
    if 0 <= midi_number <= 127:
        return midi_number - 20
    else:
        raise ValueError("midi_number must be integer between 0 and 127!")

###############################################################################
def slice_salami(midi: MidiFile):
    """Reduce to chords.

    Arguments:
    midi (MidiFile) -- A mido MidiFile

    Returns:
    List of tuples -- Each tuple is two dimensions, a list of MIDI numbers and a equivilant quarter-length duration value.

    """
    slices = []
    current_chord = set()

    for msg in midi.tracks[0]: # Type 0 assumed.
        # If time has passed, close the previous slice.
        if msg.time > 0:
            if current_chord:
                slices.append((
                    sorted(current_chord),
                    msg.time  # absolute tick duration.
                ))

        # Update chord state AFTER closing the slice.
        if msg.type == 'note_on' and msg.velocity > 0:
            current_chord.add(msg.note)

        elif msg.type == 'note_off' or (
            msg.type == 'note_on' and msg.velocity == 0
        ):
            current_chord.discard(msg.note)

        # Ignore all other message types.

    return slices

###############################################################################
def get_notes(midi: MidiFile):
    """Get discrete note durations.

    Arguments:
    midi (MidiFile) -- A mido MidiFile

    Returns:
    list of tuples -- Each tuple is a not event, with its note number, duration in ticks, and a placeholder for order.

    """
    note_events = []

    # Active notes: (channel, note) -> list of start times
    active_notes = defaultdict(list)

    for track in midi.tracks:
        absolute_time = 0

        for msg in track:
            absolute_time += msg.time

            if msg.type == 'note_on' and msg.velocity > 0:
                # Note start
                key = (msg.channel, msg.note)
                active_notes[key].append(absolute_time)

            elif msg.type in ('note_off', 'note_on') and msg.velocity == 0:
                # Note end
                key = (msg.channel, msg.note)
                if active_notes[key]:
                    start_time = active_notes[key].pop()
                    length = absolute_time - start_time
                    note_events.append((msg.note, length, None))

    return note_events

###############################################################################

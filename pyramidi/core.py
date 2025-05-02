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
def get_ticks_from_measures(mid: MidiFile, n_measures: int) -> int:
    """
    Calculate the raw tick position after counting `n_measures` bars, ignoring time from program_change messages
    when counting measures, but including their ticks in the returned raw tick value.

    Parameters
    ----------
    mid : MidiFile
        A mido MidiFile instance (must be type 0).
    n_measures : int
        The number of measures (bars) to count.

    Returns
    -------
    int
        The raw tick position at the end of the nth measure, including program_change deltas.
        If the file ends before n_measures, returns the total raw length and issues a warning.
    """
    # PPQ: ticks per quarter-note
    ppq = mid.ticks_per_beat

    # Phase 1: collect time-signature events with both raw and effective tick positions
    events = []  # tuples: (raw_tick, eff_tick, numerator, denominator)
    raw_tick = 0
    eff_tick = 0
    for msg in mid.tracks[0]:
        delta = msg.time
        raw_tick += delta
        if msg.type != 'program_change':
            eff_tick += delta
        if msg.type == 'time_signature':
            events.append((raw_tick, eff_tick, msg.numerator, msg.denominator))
    # total lengths
    total_raw = raw_tick
    total_eff = eff_tick

    # ensure an initial time signature at tick 0
    if not events or events[0][0] != 0:
        events.insert(0, (0, 0, 4, 4))
    # sentinel event at end
    events.append((total_raw, total_eff, None, None))

    # compute the effective tick where the nth measure boundary falls
    measures_counted = 0
    measure_end_eff = None
    for (start_raw, start_eff, num, denom), (next_raw, next_eff, *_) in zip(events, events[1:]):
        segment_eff = next_eff - start_eff
        # ticks per measure in this signature
        tpm = ppq * num * (4 / denom)
        full = int(segment_eff // tpm)
        if measures_counted + full >= n_measures:
            need = n_measures - measures_counted
            measure_end_eff = start_eff + need * tpm
            break
        measures_counted += full

    # if not found, warn and return full length
    if measure_end_eff is None:
        warnings.warn(
            f"File ends after {measures_counted} measures; returning full raw length ({total_raw} ticks)",
            UserWarning
        )
        return total_raw

    # Phase 2: map the effective boundary back to raw tick
    raw_tick = 0
    eff_tick = 0
    for msg in mid.tracks[0]:
        delta = msg.time
        raw_tick += delta
        if msg.type != 'program_change':
            prev_eff = eff_tick
            eff_tick += delta
            if eff_tick >= measure_end_eff:
                # boundary occurred within this delta
                overshoot = eff_tick - measure_end_eff
                boundary_delta = delta - overshoot
                return int(raw_tick - delta + boundary_delta)
    # fallback
    return total_raw

# =========================================================================== #
def pre_process(mid: MidiFile) -> MidiFile:
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
    new_mid = MidiFile(type=0, ticks_per_beat=mid.ticks_per_beat)

    # Merge all existing tracks into a single track
    merged = merge_tracks(mid.tracks)

    # Create a new track and copy merged events into it
    track0 = MidiTrack()
    track0.extend(merged)

    new_mid.tracks.append(track0)
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
    Return a new MidiFile (Type 0) containing only events up to `cut_tick`.
    """
    # make an empty MIDI with same timing
    new_mid = MidiFile(type=0)
    new_mid.ticks_per_beat = mid.ticks_per_beat

    track = MidiTrack()
    new_mid.tracks.append(track)

    cum_tick = 0
    # keep track of which notes are currently on, so we can turn them off
    active_notes = {}

    for msg in mid.tracks[0]:
        # if we've already reached or passed the cut, skip everything
        if cum_tick >= cut_tick:
            break

        # if this message would go past the cut:
        if cum_tick + msg.time > cut_tick:
            # include a truncated delta
            delta = cut_tick - cum_tick
            # insert a “dummy” message with just the delta (no real event)
            # OR attach that delta to the next meta/end_of_track
            if not msg.is_meta and msg.type.startswith('note_'):
                # we won’t include the original msg, just advance time
                track.append(Message('note_off', note=0, velocity=0, time=delta))
            else:
                # for meta (including tempo), we skip the event but absorb the time
                track.append(MetaMessage('end_of_track', time=delta))
            cum_tick = cut_tick
            break

        # otherwise, copy the message in full
        # but watch for note_on/off to track active notes
        copy = msg.copy()
        track.append(copy)
        cum_tick += msg.time

        # track active notes so we can shut them all off at the end
        if not msg.is_meta and msg.type == 'note_on' and msg.velocity > 0:
            active_notes.setdefault((msg.channel, msg.note), 0)
            active_notes[(msg.channel, msg.note)] += 1
        elif not msg.is_meta and (
              (msg.type == 'note_off') or
              (msg.type == 'note_on' and msg.velocity == 0)
            ):
            key = (msg.channel, msg.note)
            if key in active_notes:
                active_notes[key] -= 1
                if active_notes[key] <= 0:
                    del active_notes[key]

    # at cut point, make sure any still-on notes get turned off immediately
    if active_notes:
        for (chan, note), count in list(active_notes.items()):
            # velocity 0 note_on is equivalent to note_off
            track.append(Message('note_on', note=note, velocity=0,
                                 channel=chan, time=0))
        active_notes.clear()

    # finally, add a clean End-of-Track
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

"""
Tools for applying transformations to midi files.

Functions
- change_pitchHeight
- change_articulation
- change_velocity
- change_tempo
"""

###############################################################################
# Built-in Imports
from copy import deepcopy
# Third-Party Imports
from mido import MidiFile, MidiTrack, MetaMessage

__all__ = [
    "change_transposition", "change_articulation", "change_velocity",
    "change_tempo", "TransformMidi"
]

###############################################################################
class TransformMidi:
    """
    A pipeline for applying musical transformations to a mido.MidiFile.

    This class stores the original MidiFile and a list of transformation functions. When `render()` is called, it creates a deep copy of the original MIDI and applies each transformation in input order, returning the transformed MidiFile.

    Arguments:
    midi (MidiFile) -- The original MIDI file to be transformed.

    Attributes:
    midi (MidiFile) -- The original MIDI file (kept intact).
    transforms (list[tuple[callable, dict]]) -- A list of transformation functions and their keyword arguments.
    """

    def __init__(self, midi: MidiFile):
        self.midi = midi
        self.transforms = []

    def add(self, transform_fn, **kwargs):
        """Add a transformation to the pipeline.

        Arguments:
        transform_fn (callable) -- A function that takes a MidiFile and returns a transformed MidiFile.
        **kwargs -- Keyword arguments passed to transform_fn when render() is called.

        Returns
        TransformMidi -- Returns self to allow chaining.
        """
        self.transforms.append((transform_fn, kwargs))
        return self

    def render(self) -> MidiFile:
        """Apply all queued transformations to a copy of the original MIDI.

        This method does not modify the original MIDI stored in `self.midi`.

        Returns:
        MidiFile -- The transformed copy of the original MIDI.
        """
        working_midi = deepcopy(self.midi)

        for fn, kwargs in self.transforms:
            working_midi = fn(working_midi, **kwargs)

        return working_midi

###############################################################################
def change_transposition(
    midi: MidiFile,
    semitones: int = 0,
    min_note: int = 0,
    max_note: int = 127,
    octave_shift: bool = False
) -> MidiFile:
    """Transpose all pitches in a MidiFile.

    Arguments:
    midi (MidiFile) -- A mido MidiFile.
    semitones (int) -- Number of semitones to transpose.

    Returns:
    MidiFile -- A transformed mido MidiFile.

    """

    def octave_wrap(note: int) -> int:
        """If a note falls outside the range, transpose it an octave.

        Arguments:
        note (int) -- A MIDI number, the note to check

        Returns:
        int -- The valid octave shifted note

        """
        while note < min_note or note > max_note:
            if note > max_note:
                note -= 12
            elif note < min_note:
                note += 12
        return note

    if midi.type != 0:
        raise ValueError("change_ functions only support type 0 MidiFile objects.")

    # Setup new MidiFile.
    new_midi = MidiFile(type = 0, ticks_per_beat = midi.ticks_per_beat)
    new_track = MidiTrack()
    new_midi.tracks.append(new_track)

    for msg in midi.tracks[0]:
        if msg.type in ["note_on", "note_off"]:
            new_note = msg.note + semitones

            if octave_shift:
                new_note = octave_wrap(new_note)
            else:
                if new_note < min_note or new_note > max_note:
                    raise ValueError(
                        f"Transposition pushes note {msg.note} -> {new_note} "
                        f"outside valid range [{min_note},{max_note}]. "
                        f"Set octave_shift=True to auto-wrap."
                    )

            new_track.append(msg.copy(note = new_note))
        else:
            new_track.append(msg.copy())

    return new_midi

###############################################################################
def change_articulation(
    midi: MidiFile,
    articulation: float = 0.75
) -> MidiFile:
    """Shorten note durations while preserving the original timeline.

    Arguments:
    midi (MidiFile) -- Input MIDI file.
    articulation (float) -- Ratio to shorten note lengths (0 < articulation <= 1).

    Returns:
    MidiFile -- Transformed MIDI file.
    """
    if midi.type != 0:
        raise ValueError("change_ functions only support type 0 MidiFile objects.")

    if not 0 < articulation <= 1:
        raise ValueError("articulation must be between 0 and 1")

    new_midi = MidiFile(ticks_per_beat=midi.ticks_per_beat, type=0)

    for track in midi.tracks:
        abs_time = 0
        events = []

        for msg in track:
            abs_time += msg.time
            events.append((abs_time, msg.copy()))

        active_notes = {}
        new_events = []

        for time, msg in events:
            if msg.type == "note_on" and msg.velocity > 0:
                active_notes[(msg.channel, msg.note)] = time
                new_events.append((time, msg))

            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                key = (msg.channel, msg.note)
                if key in active_notes:
                    start = active_notes.pop(key)
                    duration = time - start
                    new_duration = max(1, int(duration * articulation))
                    new_off_time = start + new_duration
                    new_events.append((new_off_time, msg))
                else:
                    new_events.append((time, msg))

            else:
                new_events.append((time, msg))

        new_events.sort(key=lambda x: x[0])

        new_track = MidiTrack()
        last_time = 0
        for abs_time, msg in new_events:
            msg.time = abs_time - last_time
            new_track.append(msg)
            last_time = abs_time

        new_midi.tracks.append(new_track)

    return new_midi

###############################################################################
def change_velocity(
    midi: MidiFile,
    velocity: int = 64
) -> MidiFile:
    """Change the velocity of all notes.

    Arguments:
    midi (MidiFile) -- A mido MidiFile
    velocity (int) -- Velocity to transform, in MIDI format (must be 0 - 127)

    Returns:
    MidiFile -- A transformed mido MidiFile

    """
    if midi.type != 0:
        raise ValueError("change_ functions only support type 0 MidiFile objects.")

    if not 0 <= velocity <= 127:
        raise ValueError("velocity must be between 0 and 127")

    # Create a new MidiFile.
    new_midi = MidiFile(type = 0, ticks_per_beat = midi.ticks_per_beat)

    for track in midi.tracks:
        new_track = MidiTrack()
        for msg in track:
            if msg.type == "note_on" and msg.velocity > 0:
                new_track.append(msg.copy(velocity = int(velocity)))
            else:
                new_track.append(msg.copy()) # Copy other messages as they are.

        new_midi.tracks.append(new_track)

    return new_midi

###############################################################################
def change_tempo(midi: MidiFile, tempo: int = 500000) -> MidiFile:
    """ Change the tempo of an entire MidiFile.

    Arguments:
    midi (MidiFile) -- A mido MidiFile
    tempo (int) -- Tempo to transform, in microseconds per quarter note.

    Returns:
    MidiFile -- A transformed mido MidiFile

    """

    if midi.type != 0:
        raise ValueError("change_ functions only support type 0 MidiFile objects.")

    # Create a new MidiFile.
    new_midi = MidiFile(type = 0, ticks_per_beat = midi.ticks_per_beat)

    for i, track in enumerate(midi.tracks):
        new_track = MidiTrack()
        saw_tempo = False

        for msg in track:
            if msg.type == "set_tempo":
                new_track.append(msg.copy(tempo = tempo))
                saw_tempo = True
            else:
                new_track.append(msg.copy()) # Copy other messages as they are.

        if i == 0 and not saw_tempo:
            new_track.insert(
                0,
                MetaMessage('set_tempo', tempo = tempo, time = 0)
            )

        new_midi.tracks.append(new_track)

    return new_midi
###############################################################################

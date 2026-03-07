"""
Procedurally change `PyraMIDIFile` objects.

Change individual aspects of a MIDI file, or create a pipeline to change multiple aspects. Classes prefaced with `Set` overwrite existing values, while those prefaced with `Transform` take the current values and alter them by adding, multiplying, etc. Use `change_midi`

Change Classes:
    - `SetVelocity`
    - `TransformVelocity`
    - `TransformPitch`
    - `TransformArticulation`
    - `TransformTempo`
    - `SetTempo`

Example:
    ```
    from pyramidi import PyraMIDIFile, change_midi
    from pyramidi.transform import SetVelocity, TransformTempo, SetArticulation, SetTransposition

    midi = PyraMIDIFile("your_midi_file.mid")

    change_vector = [
        SetVelocity(120), # Set all note velocities to 120.
        TransformTempo(1.25), # Increase the tempo by 25%.
        SetArticulation(0.75), # Play all notes 75% of their full duration.
        SetTransposition(2), # Transpose all notes by a whole tone.
    ]

    new_midi = change_midi(change_vector, midi)
    new_midi.save("pyramidi_example.mid")
    ```

Use Abstract Class `ChangeMIDI` to create new changes.
"""
# TODO: Standardize Type 1 and Type 0 compatibility.
# TODO: Use expressions instead of method for Transform.

# =========================================================================== #
# Built-in Imports.
from abc import ABC, abstractmethod
from typing import Any, List, Dict

# Third Party Imports.
from mido import MidiFile, MidiTrack, MetaMessage

# Local Imports
from . import PyraMIDIFile

__all__ = [
    "SetVelocity",
    "TransformVelocity",
    "TransformPitch",
    "TransformArticulation",
    "TransformTempo",
    "SetTempo",
    "change_midi"
]

# =========================================================================== #
class ChangeMIDI(ABC):
    """
    Abstract Class for altering PyraMIDIFIle instances. Subclasses should be named with a 'VerbMIDI' pattern: if the change overwrites an existing aspect of the MIDI, use 'Set'. If it changes existing aspects by adding, multiplying, etc., use 'change'. __init__ should accept any arguments necessary to specify how the transformation is performed, and validate those arguments on instantiation.
    """
    @abstractmethod
    def change(self, midi: PyraMIDIFile) -> PyraMIDIFile:
        """Change a PyraMIDIFile.

        Arguments:
        midi (PyraMIDIFile) -- The midi data to be changed.

        Returns:
        PyraMIDIFIle -- Changed midi.

        """

    def __call__(self, midi: PyraMIDIFile) -> PyraMIDIFile:
        """Run the change method on class call.

        Returns:
        PyraMIDIFIle -- Changed midi.

        """
        return self.change(midi)

    @abstractmethod
    def to_spec(self) -> Dict[str, Any]:
        """Specify the change.

        Returns:
        Dict[str, Any] -- A dictionary of all information needed to reproduce an instance of the Change class, including the class name.
        """


# =========================================================================== #
def _new_midi_like(midi: PyraMIDIFile) -> MidiFile:
    """Create a new MidiFile with the same structural properties."""
    return MidiFile(type=midi.type, ticks_per_beat=midi.ticks_per_beat)

# =========================================================================== #
def change_midi(
    change_vector: List[ChangeMIDI],
    midi: PyraMIDIFile
):
    """Perform a pipeline of ChangeMIDI to PyraMIDIFile."""
    transformed_midi = midi

    for transformation in change_vector:
        if not isinstance(transformation, ChangeMIDI):
            raise TypeError("All elements of change_vector must be ChangeMIDI objects")
        transformed_midi = transformation(transformed_midi)

    return transformed_midi

# =========================================================================== #
class SetVelocity(ChangeMIDI):
    """Overwrite the velocity of all note_on > 1 with one value."""
    def __init__(self, velocity: int = 64):
        """Instantiate and validate a change.
        
        Arguments:
        velocity (int) [1, 127] -- Velocity value to use for replacement.

        """
        if not isinstance(velocity, int) or not 1 <= velocity <= 127:
            raise ValueError("velocity must be an integer between 1 and 127")
        self.velocity = velocity

    def change(self, midi: PyraMIDIFile):
        if midi.type == 2:
            raise ValueError("MIDI must not be type 2.")

        transformed_midi = _new_midi_like(midi)

        for track in midi.tracks:
            new_track = MidiTrack()

            for msg in track:
                if msg.type == "note_on" and msg.velocity > 0:
                    new_track.append(msg.copy(velocity=self.velocity))
                else:
                    new_track.append(msg.copy())

            transformed_midi.tracks.append(new_track)

        return transformed_midi

    def to_spec(self):
        return {
            "type": self.__class__.__name__,
            "velocity": self.velocity
        }

# =========================================================================== #
class TransformVelocity(ChangeMIDI):
    """Change the velocity of all note on > 0 functionally."""
    def __init__(self, amount: int = 0, method: str = "add"):
        """Instantiate and validate a change.
        
        Arguments:
        amount (int) -- Value used to alter velocity.
        method (str) -- How to alter the velocity. `add` or `multiply`.

        """
        if not isinstance(amount, int):
            raise ValueError("amount must be an integer")

        if method not in {"add", "multiply"}:
            raise ValueError("method must be 'add' or 'multiply'")

        self.amount = amount
        self.method = method

    def _apply(self, velocity: int) -> int:
        """Apply a specified method."""
        if self.method == "add":
            new_velocity = velocity + self.amount

        elif self.method == "multiply":
            new_velocity = velocity * self.amount

        else:
            raise ValueError("Unsupported method")

        if not 1 <= new_velocity <= 127:
            raise ValueError(
                f"Transformed velocity {new_velocity} is outside valid MIDI range (1–127)"
            )

        return int(new_velocity)

    def change(self, midi: PyraMIDIFile):
        if midi.type == 2:
            raise ValueError("MIDI must not be type 2.")

        transformed_midi = _new_midi_like(midi)

        for track in midi.tracks:
            new_track = MidiTrack()

            for msg in track:
                if msg.type == "note_on" and msg.velocity > 0:
                    new_velocity = self._apply(msg.velocity)
                    new_track.append(msg.copy(velocity=new_velocity))
                else:
                    new_track.append(msg.copy())

            transformed_midi.tracks.append(new_track)

        return transformed_midi

    def to_spec(self):
        return {
            "type": self.__class__.__name__,
            "amount": self.amount,
            "method": self.method
        }

# =========================================================================== #
class TransformPitch(ChangeMIDI):
    """Change the note of all events functionally."""
    def __init__(
        self,
        amount: int = 0,
        method: str = "add",
        min_note: int = 0,
        max_note: int = 127,
        octave_shift: bool = False
    ):
        """Instantiate and validate a change.
        
        Arguments:
        amount (int) --
        method (str) --
        min_note (int) [0-128] --
        max_note (int) [0-128] --
        octave_shift (bool) -- 

        """
        if not isinstance(amount, int):
            raise ValueError("amount must be an integer")

        if method not in {"add", "multiply"}:
            raise ValueError("method must be 'add' or 'multiply'")

        if not isinstance(min_note, int) or not 0 <= min_note <= 127:
            raise ValueError("min_note must be an integer between 0 and 127")

        if not isinstance(max_note, int) or not 0 <= max_note <= 127:
            raise ValueError("max_note must be an integer between 0 and 127")

        if min_note > max_note:
            raise ValueError("min_note must be <= max_note")

        if not isinstance(octave_shift, bool):
            raise ValueError("octave_shift must be True or False")

        self.amount = amount
        self.method = method
        self.min_note = min_note
        self.max_note = max_note
        self.octave_shift = octave_shift

    def _apply(self, note: int) -> int:
        """Apply a specified method."""
        if self.method == "add":
            return note + self.amount

        elif self.method == "multiply":
            return note * self.amount

        raise ValueError("Unsupported method")

    def _octave_wrap(self, note: int) -> int:
        """Adjust octave if out of range (OPTIONAL)."""
        while note < self.min_note or note > self.max_note:

            if note > self.max_note:
                note -= 12

            elif note < self.min_note:
                note += 12

        return note

    def change(self, midi: PyraMIDIFile):
        if midi.type != 0:
            raise ValueError("Only supports type 0 MidiFile objects.")

        transformed_midi = _new_midi_like(midi)
        new_track = MidiTrack()
        transformed_midi.tracks.append(new_track)

        for msg in midi.tracks[0]:

            if msg.type in ("note_on", "note_off"):

                new_note = self._apply(msg.note)

                if self.octave_shift:
                    new_note = self._octave_wrap(new_note)

                else:
                    if not self.min_note <= new_note <= self.max_note:
                        raise ValueError(
                            f"Pitch change pushes note {msg.note} -> {new_note} "
                            f"outside valid range [{self.min_note}, {self.max_note}]. "
                            f"Set octave_shift=True to auto-wrap."
                        )

                new_track.append(msg.copy(note=new_note))

            else:
                new_track.append(msg.copy())

        return transformed_midi

    def to_spec(self):
        return {
            "type": self.__class__.__name__,
            "amount": self.amount,
            "method": self.method,
            "min_note": self.min_note,
            "max_note": self.max_note,
            "octave_shift": self.octave_shift
        }

# =========================================================================== #
class TransformArticulation(ChangeMIDI):
    """Change the duration of all notes without altering the rhythmic structure."""
    # TODO: Looks like there is a lower limit to this. Worth knowing what it is... Maybe software dependant?
    def __init__(self, articulation: float = 1):
        """Instantiate and validate a change.
        
        Arguments:
        articulation (float) -- Proportion of full note duration to be played.

        """
        if not isinstance(articulation, (int, float)) or not (0 < articulation <= 1):
            raise ValueError(
                "articulation must be a number greater than 0 and less than or equal to 1."
            )

        self.articulation = articulation

    def change(self, midi: PyraMIDIFile):
        if midi.type != 0:
            raise ValueError("Only supports type 0 PyraMIDIFile objects.")

        transformed_midi = _new_midi_like(midi)

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
                        new_duration = max(1, int(duration * self.articulation))
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

            transformed_midi.tracks.append(new_track)

        return transformed_midi

    def to_spec(self):
        return {
            "type": self.__class__.__name__,
            "articulation": self.articulation
        }

# =========================================================================== #
class TransformTempo(ChangeMIDI):
    """Change the tempo functionally."""
    def __init__(self, tempo_ratio: float = 1):
        """Instantiate and validate a change.
        
        Arguments:
        tempo_ratio (float) -- Proportion of current tempo to change.

        """
        if not isinstance(tempo_ratio, (int, float)) or tempo_ratio <= 0:
            raise ValueError("tempo_ratio must be a positive number greater than 0.")

        self.tempo_ratio = tempo_ratio

    def change(self, midi: PyraMIDIFile):
        if midi.type != 0:
            raise ValueError("TransformTempo only supports type 0 MidiFile objects.")

        saw_tempo = False
        transformed_midi = _new_midi_like(midi)

        for track in midi.tracks:

            new_track = MidiTrack()

            for msg in track:

                if msg.type == "set_tempo":

                    saw_tempo = True
                    new_tempo = int(msg.tempo / self.tempo_ratio)
                    new_track.append(msg.copy(tempo=new_tempo))

                else:
                    new_track.append(msg.copy())

            transformed_midi.tracks.append(new_track)

        if not saw_tempo:
            raise ValueError("No tempo events found in MIDI file. Cannot scale tempo.")

        return transformed_midi

    def to_spec(self):
        return {
            "type": self.__class__.__name__,
            "tempo_ratio": self.tempo_ratio
        }

# =========================================================================== #
class SetTempo(ChangeMIDI):
    """Overwrite all tempi with a constant."""
    def __init__(self, tempo: int):
        """Instantiate and validate a change.
        
        Arguments:
        tempo (int) -- Tempo to overwrite, in microseconds per quarter note.

        """
        if not isinstance(tempo, int) or tempo <= 0:
            raise ValueError("tempo must be an integer greater than 0.")

        self.tempo = tempo

    def change(self, midi: PyraMIDIFile):
        if midi.type != 0:
            raise ValueError("SetmTempo only supports type 0 MidiFile objects.")

        transformed_midi = _new_midi_like(midi)

        for track in midi.tracks:

            new_track = MidiTrack()
            saw_tempo = False

            for msg in track:

                if msg.type == "set_tempo":

                    new_track.append(msg.copy(tempo=self.tempo))
                    saw_tempo = True

                else:
                    new_track.append(msg.copy())

            if not saw_tempo:
                new_track.insert(0, MetaMessage("set_tempo", tempo=self.tempo, time=0))

            transformed_midi.tracks.append(new_track)

        return transformed_midi

    def to_spec(self):
        return {
            "type": self.__class__.__name__,
            "tempo": self.tempo
        }

# =========================================================================== #

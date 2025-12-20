"""
Tools for applying transformations to midi files.

Functions
- change_pitchHeight
- change_articulation
- change_velocity
- change_tempo
"""
###############################################################################
# Third-Party Imports
from mido import MidiFile, MidiTrack, MetaMessage

###############################################################################
# THIS NEEDS REWORKING.
class ManipulateMIDI:
    """
    """
    def __init__(
        self,
        midi_file: str,
        output_file: str = "output.mid",
        file = True
    ):
        """
        """
        self.midi_file = midi_file
        self.output_file = output_file
        if file == True:
            self.midi = MidiFile(midi_file)
        else:
            self.midi = midi_file
        self.manipulated_midi = None
    ###########################################################################
    def __str__(self):
        """
        """
        return self.midi_file
    ###########################################################################
    def manipulate(
        self,
        tempo: float = 120,
        semitones: int = 0,
        min_pitch: int = 0,
        max_pitch: int = 127,
        velocity: int = 64,
        articulation: float = 1
    ):
        """
        """
        self.manipulated_midi = change_bpm(
            self.midi,
            bpm = tempo
        )
        self.manipulated_midi = change_pitchHeight(
            self.manipulated_midi,
            semitones = semitones,
            min = min_pitch,
            max = max_pitch
        )
        self.manipulated_midi = change_velocity(
            self.manipulated_midi,
            velocity = velocity
        )
        # TODO: make change_articulation work
        #self.manipulated_midi = change_articulation(self.manipulated_mid,
        #                                           articulation = articulation)
    ###########################################################################
    def export(self):
        """
        """
        self.manipulated_midi.save(self.output_file)
    ###########################################################################
    def qwik(self,
             tempo: float = 120,
             semitones: int = 0,
             min_pitch: int = 0,
             max_pitch: int = 127,
             velocity: int = 64,
             articulation: float = 1):
        """
        """
        self.manipulate(tempo = tempo,
                        semitones = semitones,
                        min_pitch = 0,
                        max_pitch = 127,
                        velocity = velocity,
                        articulation = articulation)
        self.export()
    
###############################################################################
def change_pitchHeight(
    midi: MidiFile,
    semitones: int = 0,
    min: int = 0,
    max: int = 127
):
    """Transpose all pitches in a MidiFile.

    Arguments:
    midi (MidiFile) -- A mido MidiFile
    semitones (int) -- Number of semitones to transpose.

    Returns:
    MidiFile -- A transformed mido MidiFile

    """
    def check_midiNo(note: int, min: int = 0, max: int = 127):
        """Check if a MIDI number fits in a range.

        Arguments:
        note (int) -- A MIDI number, the note to check
        min (int) -- Minimum MIDI number allowed, usually the bottom limit of a sound font
        max (int) -- Maximum MIDI number allowed, usually the bottom limit of a sound font


        Returns:
        int -- The valid octave shifted note

        Not as relevant anymore.
        """
        # Adjust the note until it's within the valid range.
        while note < min or note > max:
            if note > max:
                note -= 12  # Adjust note by subtracting an octave.
            elif note < min:
                note += 12  # Adjust note by adding an octave.

        return note  # Return the valid note.

    ############################################################################
    # TODO: Add arg for only allowed note range.
    new_midi = MidiFile(type = 0, ticks_per_beat = midi.ticks_per_beat)
    track = MidiTrack()
    new_midi.tracks.append(track)
    for i in range(len(midi.tracks)):
        for msg in midi.tracks[i]:
            if msg.type in ["note_on", "note_off"]:
                new_note = check_midiNo(
                    msg.note + semitones, 
                    min = min,
                    max = max
                )
                track.append(msg.copy(note = new_note))
            else:
                track.append(msg)   
    return new_midi

###############################################################################
def change_articulation(
    midi_file: MidiFile,
    articulation: float = 0.75
):
    """Change the 'on' duration of all note messages.

    Arguments:
    midi (MidiFile) -- A mido MidiFile
    articulation (int) -- Articulation factor, a proportion of 1

    Returns:
    MidiFile -- A transformed mido MidiFile

    """
    # TODO: ADD CHECK FOR > 0 < 1
    new_mid = MidiFile(ticks_per_beat=midi_file.ticks_per_beat)

    for track in midi_file.tracks:
        abs_time = 0
        events = []

        for msg in track:
            abs_time += msg.time
            events.append((abs_time, msg.copy()))

        active_notes = {}
        new_events = []

        for time, msg in events:
            if msg.type == 'note_on' and msg.velocity > 0:
                active_notes[(msg.channel, msg.note)] = time
                new_events.append((time, msg))

            elif (
                msg.type == 'note_off'
                or (msg.type == 'note_on' and msg.velocity == 0)
            ):
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

        new_mid.tracks.append(new_track)

    return new_mid

###############################################################################
def change_velocity(
    midi: MidiFile,
    velocity: int = 64
):
    """Change the velocity of all notes.

    Arguments:
    midi (MidiFile) -- A mido MidiFile
    velocity (int) -- Velocity to transform, in MIDI format (must be 0 - 127)

    Returns:
    MidiFile -- A transformed mido MidiFile

    """
    # TODO: Check values for 0-127
    # Create a new MidiFile with the same ticks_per_beat.
    new_midi = MidiFile(type = 0, ticks_per_beat = midi.ticks_per_beat)
    track = MidiTrack()
    new_midi.tracks.append(track)

    # Iterate over each track and its messages.
    for i in range(len(midi.tracks)):
        for msg in midi.tracks[i]:
            if msg.type == "note_on":
                # Check if the current velocity is greater than 0 before changing.
                if msg.velocity > 0:
                    track.append(msg.copy(velocity = int(velocity)))  # Apply new velocity.
                else:
                    track.append(msg)  # Leave the message as is.
            else:
                track.append(msg)  # Copy other messages as they are.

    return new_midi

###############################################################################
def change_tempo(
    midi: MidiFile,
    tempo: int = 500000
):
    """ Change the tempo of an entire MidiFile.

    Arguments:
    midi (MidiFile) -- A mido MidiFile
    tempo (int) -- Tempo to transform, in microseconds per quarter note.

    Returns:
    MidiFile -- A transformed mido MidiFile

    """
    # Create a new MidiFile with the same ticks_per_beat.
    new_midi = MidiFile(type = 0, ticks_per_beat = midi.ticks_per_beat)
    track = MidiTrack()
    new_midi.tracks.append(track)

    saw_tempo = False

    # Iterate over each track and its messages.
    for i in range(len(midi.tracks)):
        for msg in midi.tracks[i]:
            if msg.type == "set_tempo":
                # Replace tempo with the specified value.
                track.append(msg.copy(tempo = tempo))
                saw_tempo = True
            else:
                track.append(msg)  # Copy other messages as they are.
    
    if not saw_tempo:
        track.insert(3, MetaMessage('set_tempo', tempo = tempo, time = 0))

    return new_midi

###############################################################################

"""
"""
###############################################################################
# Third-Party Imports
from mido import MidiFile, MidiTrack, bpm2tempo
###############################################################################
# Constants
__all__ = ['ManipulateMIDI']
###############################################################################
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

########################################################################
def check_midiNo(note: int, min: int = 0, max: int = 127):
    """
    Ensures that a MIDI note number is within the valid range (min to max).
    
    This function checks if the given MIDI note falls within the specified range of 
    allowed MIDI note numbers (by default 0 to 127). If the note is outside the range, 
    it adjusts the note by shifting it by an octave (12 semitones) until it is within the range.
    
    The function recursively adjusts the note by adding or subtracting octaves (12 semitones) 
    as needed to ensure the note falls between the `min` and `max` values.

    Parameters:
        note (int): The MIDI note number to check. MIDI notes are integers, with 0 being the lowest note.
        min (int, optional): The minimum valid MIDI note number. Default is 0.
        max (int, optional): The maximum valid MIDI note number. Default is 127.

    Returns:
        int: The adjusted MIDI note number, within the specified range.

    Example:
        note = check_midiNo(130)   # Will return 118 (130 - 12 = 118).
        note = check_midiNo(-5)    # Will return 7 (-5 + 12 = 7).
    """
    # Adjust the note until it's within the valid range
    while note < min or note > max:
        if note > max:
            note -= 12  # Adjust note by subtracting an octave
        elif note < min:
            note += 12  # Adjust note by adding an octave

    return note  # Return the valid note
    
###############################################################################
def change_pitchHeight(
    midiFile: str,
    semitones = 0,
    min: int = 0,
    max: int = 127
):
    """
    """
    #midiFile = MidiFile (midiFile)
    new = MidiFile(type=0, ticks_per_beat = midiFile.ticks_per_beat)
    track = MidiTrack()
    new.tracks.append(track)
    for i in range(len(midiFile.tracks)):
        for msg in midiFile.tracks[i]:
            if msg.type in ["note_on", "note_off"]:
                new_note = check_midiNo(
                    msg.note + semitones, 
                    min = min,
                    max = max
                )
                track.append(msg.copy(note = new_note))
            else:
                track.append(msg)   
    return new

###############################################################################
def change_velocity(midiFile: MidiFile, velocity = 64):
    """
    Changes the velocity of all 'note_on' events in the MIDI file to a specified value,
    only if the current velocity is greater than 0.

    Parameters:
        midiFile (mido.MidiFile): The original MIDI file.
        velocity (int): The new velocity value to set for 'note_on' events.
        
    Returns:
        mido.MidiFile: A new MIDI file with the modified velocities.
    """
    # Create a new MidiFile with the same ticks_per_beat
    new = MidiFile(type=0, ticks_per_beat=midiFile.ticks_per_beat)
    track = MidiTrack()
    new.tracks.append(track)

    # Iterate over each track and its messages
    for i in range(len(midiFile.tracks)):
        for msg in midiFile.tracks[i]:
            if msg.type == "note_on":
                # Check if the current velocity is greater than 0 before changing
                if msg.velocity > 0:
                    track.append(msg.copy(velocity=int(velocity)))  # Apply new velocity
                else:
                    track.append(msg)  # Leave the message as is
            else:
                track.append(msg)  # Copy other messages as they are

    return new

###############################################################################
def change_tempo(midiFile: MidiFile, tempo: int = 500000):
    """
    Changes the tempo of all 'set_tempo' events in a MIDI file to a specified value.

    This function creates a new MIDI file with the same structure as the original, 
    but with the tempo of all 'set_tempo' events replaced by the given `tempo` value.
    The `tempo` is specified in microseconds per quarter note. If no `tempo` is provided, 
    it defaults to 500000 (which corresponds to 120 beats per minute).

    Parameters:
        midiFile (mido.MidiFile): The original MIDI file to modify.
        tempo (int, optional): The new tempo value to set for all 'set_tempo' events.
                               The default is 500000 (representing 120 beats per minute).

    Returns:
        mido.MidiFile: A new MIDI file with the modified tempo events.
        
    Example:
        midi = mido.MidiFile('input.mid')
        modified_midi = change_tempo(midi, tempo=600000)  # Set tempo to 100 BPM
        modified_midi.save('output.mid')
    """
    # Create a new MidiFile with the same ticks_per_beat
    new = MidiFile(type=0, ticks_per_beat=midiFile.ticks_per_beat)
    track = MidiTrack()
    new.tracks.append(track)

    # Iterate over each track and its messages
    for i in range(len(midiFile.tracks)):
        for msg in midiFile.tracks[i]:
            if msg.type == "set_tempo":
                # Replace tempo with the specified value
                track.append(msg.copy(tempo=tempo))
            else:
                track.append(msg)  # Copy other messages as they are

    return new

###############################################################################\
# DEV
def change_articulation(midiFile: str, duration: float = 1):
    """
    """
    #midiFile = MidiFile (midiFile)
    new = MidiFile(type=0, ticks_per_beat = midiFile.ticks_per_beat)
    track = MidiTrack()
    new.tracks.append(track)
    for i in range(len(midiFile.tracks)):
        for msg in midiFile.tracks[i]:
            if msg.type in ["note_on", "note_off"]:
                if msg.time > 0:
                    track.append(msg.copy(time = int(msg.time * duration)))
                else: 
                    track.append(msg)
            else:
                track.append(msg)
    return new

"""
abs_time = 0
for i in range(len(midiFile.tracks)):
    for msg in midiFile.tracks[i]:
        abs_time = abs_time + msg.time
        print(msg.copy(time = abs_time))
        if msg.type == "note_on":
            for next_msg in midiFile.tracks[i][index + 1:]:
                if msg.type == "note_off" or msg.velocity == 0:
                    pass
"""           
###############################################################################
def export(midiFile, filename):
    """
    """
    midiFile.save(filename)

###############################################################################
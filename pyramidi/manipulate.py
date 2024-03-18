"""
"""
###############################################################################
# Third-Party Imports
from mido import MidiFile, MidiTrack
###############################################################################
# Constants
__all__ = ['manipulate_midi']
###############################################################################
class ManipulateMIDI:
    """
    """
    def __init__(self,
                 midi_file: str,
                 output_file: str = "output.mid"):
        """
        """
        self.midi_file = midi_file
        self.output_file = output_file
        self.midi = MidiFile(midi_file)
        self.manipulated_midi = None
    ###########################################################################
    def __str__(self):
        """
        """
        return self.midi_file
    ###########################################################################
    def manipulate(self,
                   tempo = 1,
                   semitones: int = 0,
                   min_pitch: int = 0,
                   max_pitch: int = 127,
                   velocity: int = 64,
                   articulation: float = 1):
        """
        """
        self.manipulated_midi = change_tempo(self.midi,
                                             tempo = tempo)
        self.manipulated_midi = change_pitchHeight(self.manipulated_midi,
                                                   semitones = semitones,
                                                   min = min_pitch,
                                                   max = max_pitch)
        self.manipulated_midi = change_velocity(self.manipulated_midi,
                                                velocity = velocity)
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
             tempo = 1,
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
    """
    if note > max:
        new_note = check_midiNo(note - 12)
        return new_note
    elif note < min:
        new_note = check_midiNo(note + 12)
        return new_note
    else: return note
    
###############################################################################
def change_pitchHeight(midiFile: str,
                      semitones = 0,
                      min: int = 0,
                      max: int = 127):
    """
    """
    #midiFile = MidiFile (midiFile)
    new = MidiFile(type=0, ticks_per_beat = midiFile.ticks_per_beat)
    track = MidiTrack()
    new.tracks.append(track)
    for i in range(len(midiFile.tracks)):
        for msg in midiFile.tracks[i]:
            if msg.type in ["note_on", "note_off"]:
                new_note = check_midiNo(msg.note + semitones, 
                                       min = min, max = max)
                track.append(msg.copy(note = new_note))
            else:
                track.append(msg)   
    return new

###############################################################################
def change_velocity(midiFile: str, velocity = 64):
    """
    """
    #midiFile = MidiFile(midiFile)
    new = MidiFile(type=0, ticks_per_beat = midiFile.ticks_per_beat)
    track = MidiTrack()
    new.tracks.append(track)
    for i in range(len(midiFile.tracks)):
        for msg in midiFile.tracks[i]:
            if msg.type == "note_on":
                track.append(msg.copy(velocity = int(velocity)))
            else:
                track.append(msg)   
    return new

###############################################################################
def change_tempo(midiFile: str, tempo: float = 2.0):
    """
        MIDI tempo is given in microseconds per quarter note
        when multiplying the tempo of a file:
        numbers below 1 will decrease the microseconds per quarter note, 
        speeding up the file
        numbers above 1 will increse the microseconds per quarter note, 
        slowing down the file
        Intuitively, we thinking of a number above 1 increasing the tempo, 
        and below decreasing.
        Therefore, we take 1/a of the tempo multiplier argument 
        so it makes sense to the user.
    """
    #midiFile = MidiFile (midiFile)
    new = MidiFile(type=0, ticks_per_beat = midiFile.ticks_per_beat)
    track = MidiTrack()
    new.tracks.append(track)
    for i in range(len(midiFile.tracks)):
        for msg in midiFile.tracks[i]:
            if msg.type == "set_tempo":
                newTempo = int(msg.tempo * (1/tempo))
                track.append(msg.copy(tempo = (newTempo)))
            else:
                track.append(msg)
    return new

###############################################################################
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
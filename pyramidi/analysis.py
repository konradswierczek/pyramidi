"""
"""
###############################################################################
# Local Imports
# Third Party Imports
from mido import MidiFile, tempo2bpm, MidiTrack
from itertools import combinations
###############################################################################
# Constants
__all__ = []
maj = tuple([{(pitch + pc)%12 for pitch in [0,4,7]} for pc in range (0,12)])
min = tuple([{(pitch + pc)%12 for pitch in [0,3,7]} for pc in range (0,12)])
aug = tuple([{(pitch + pc)%12 for pitch in [0,4,8]} for pc in range (0,12)])
dim = tuple([{(pitch + pc)%12 for pitch in [0,3,6]} for pc in range (0,12)])
# Interval Vectors of various chord identities. 
CHORD_IVS = {
                # Triads
                '[0, 0, 1, 1, 1, 0]': ['maj','min'],
                '[0, 0, 2, 0, 0, 1]': 'dim',
                '[0, 0, 0, 3, 0, 0]': 'aug',
                '[0, 1, 0, 0, 2, 0]': ['sus2','sus4'],
                # Tetrads
                '[1, 0, 1, 2, 2, 0]': 'maj7',
                '[0, 1, 2, 1, 2, 0]': 'min7',
                '[1, 0, 1, 3, 1, 0]': 'minmaj7',
                '[0, 1, 2, 1, 1, 1]': ['7','min7b5'],                
                '[0, 0, 4, 0, 0, 2]': 'dim7',
                '[0, 2, 0, 2, 0, 2]': '7b5',
                '[0, 2, 1, 1, 2, 0]': 'majadd9',
                '[1, 1, 1, 1, 2, 0]': 'minadd9',
                # Pentads
                '[0, 3, 2, 1, 4, 0]': 'maj6/9',
                '[2, 1, 1, 2, 3, 1]': 'min6/9',
                '[1, 2, 2, 2, 3, 0]': ['maj9', 'min9'],
                '[2, 1, 1, 2, 3, 1]': 'maj7#11',
                '[1, 1, 3, 2, 2, 1]': '7#9',
                '[0, 3, 2, 2, 2, 1]': '9',
                '[1, 1, 4, 1, 1, 2]': '7b9',
                # Sextads
                '[2, 5, 4, 3, 6, 1]': '13',
                # TODO: #5#9, #5b9, 7sus4, min11, 7sus2?, 6?, 13s?
            }   

# Bass Interval profiles of chords with non-unique Interval Vectors. 
CHORD_BASSINT = {(4,7):'maj', (3,8):'maj', (5,9):'maj', 
                 (3,7):'min', (4,9):'min', (5,8):'min', 
                 (2,7):'sus', (5,10):'sus', (5,7):'sus', 
                 # How do you tell the difference between sus2 and sus4?
                 (3,6,10):'min7b5', (3,7,9):'min7b5', (4,6,9):'min7b5', (2,5,8):'min7b5', 
                 (4,7,10):'7', (3,6,8):'7', (3,5,9):'7', (2,6,9):'7'
                }

# Note spellings of 12-tone scale for every key. 
NOTE_KEYS = {'Cmaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'C#maj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Dbmaj':{0:'C',1:'Db',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Dmaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'D#maj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Ebmaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Emaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Fmaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'F#maj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Gbmaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Gmaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'G#maj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Abmaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Amaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'A#maj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Bbmaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Bmaj':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Cmin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'C#min':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Dbmin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Dmin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'D#min':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Ebmin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Emin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Fmin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'F#min':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Gbmin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Gmin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'G#min':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Abmin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Amin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'A#min':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Bbmin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},
             'Bmin':{0:'C',1:'C#',2:'D',3:'D#',4:'E',5:'F',6:'F#',
                     7:'G',8:'G#',9:'A',10:'A#',11:'B'},  
            }

ALLIC = list(range(0,12))
###############################################################################
def swierckj_pcd(midiFile, timebase = "seconds", velocity = "False"):
    """
    """
    # TODO: Add vleocity weightings
    midiFile = MidiFile(midiFile)
    tpb = midiFile.ticks_per_beat
    if "set_tempo" in [msg.type for msg in midiFile.tracks[0]]:
        bpm = tempo2bpm([msg.tempo for msg in midiFile.tracks[0] if 
                            msg.type == "set_tempo"][0])
    else:
        bpm = 120
    if timebase == "seconds":
        temp = 0
        new = MidiFile(type=0, ticks_per_beat = midiFile.ticks_per_beat)
        track = MidiTrack()
        new.tracks.append(track)
        for i in range(len(midiFile.tracks)):
                for msg in midiFile.tracks[i]:
                    tick_time = ((msg.time / tpb) / bpm) * 60
                    abs_time = tick_time + temp
                    track.append(msg.copy(time = abs_time))
                    temp = abs_time
    elif timebase == "ticks":
        temp = 0
        new = MidiFile(type=0, ticks_per_beat = midiFile.ticks_per_beat)
        track = MidiTrack()
        new.tracks.append(track)
        for i in range(len(midiFile.tracks)):
                for msg in midiFile.tracks[i]:
                    tick_time = msg.time
                    abs_time = tick_time + temp
                    track.append(msg.copy(time = abs_time))
                    temp = abs_time
    out = []
    for i, msg in enumerate(new.tracks[0]):
        if msg.type == "note_on":
            for next in range(i + 1, len(new.tracks[0])):
                if new.tracks[0][next].type in ["note_off", "note_on"] and new.tracks[0][next].note == msg.note:
                    out.append({"note": msg.note,
                                "velocity": msg.velocity,
                                "time_on": msg.time,
                                "time_off": new.tracks[0][next].time,
                                "length": (new.tracks[0][next].time - msg.time)})
                    break
    pcd = dict.fromkeys(range(0,12), 0)
    for msg in out:
        pc = msg["note"]%12
        pcd[pc] = pcd[pc] + msg["length"]
    return {pc: pcd[pc]/sum(pcd.values()) for pc in range(0,12)}

###############################################################################
def ambitus(file):
    """
    """
    number_list = []
    for track in MidiFile(file).tracks:
        for msg in track:
            if msg.type == "note_on":
                number_list.append(msg.note)
    return min(number_list), max(number_list)

###############################################################################

def unique_pc(chord):
        """ Returns tuple of unique pitch classes in a chord.
            chord = list of MIDI or pitch class numbers representing a chord
        """
        return set([note%12 for note in chord])

def bass_intervals(chord):
        """ Returns tuple of semitone distances between lowest note in a chord
            and every other note in the chord. 
            chord = list of MIDI or pitch class numbers representing a chord
        """
        int = [abs(chord[0]-chord[note])%12 for note in range(1,len(chord))]
        if 0 in int:
                int.remove(0)
                return tuple(int)
        else: 
                return tuple(int)

def interval_vector(chord):
        """ Returns Interval Vector of a chord after Forte 1973.
            chord = list of MIDI or pitch class numbers representing a chord
        """
        
        combos = list(combinations(unique_pc(chord),2))
        intervals = [abs(pitch[0]- pitch[1])%12 for pitch in combos]
        for ind,interval in enumerate(intervals):
                if interval > 6:
                        intervals[ind] = 12 - intervals[ind]
        intervalvector = [0 for i in range(6)]
        for interval in intervals:
                intervalvector[interval-1] = intervalvector[interval-1] + 1
        return intervalvector

def chord_quality(chord):
        """ Returns chord quality for chord symbols. See 'CHORD_IVS' for list. 
            chord = list of MIDI or pitch class numbers representing a chord
        """
        try:
                quality = CHORD_IVS[str(interval_vector(chord))]
                if type(quality) is list:
                        return CHORD_BASSINT[bass_intervals(chord)]
                else:
                        return quality
        except KeyError:
                return None

class ChordDetect:
    def __init__ (self, chord, key = 'Cmaj'):
        """ Returns chord symbol information for chord
            chord = list of MIDI or pitch class numbers representing a chord
            key = Upper-Case A-G followed by 'maj' (major) or 'min' (minor)
        """
        # What are the unique pitch classes in the chord?
        self.unique_pc = unique_pc(chord)
        # How many unique pitch classes are in the chord?
        self.cardinality = len(self.unique_pc)
        # Less than 3 notes = no chord symbol
        if self.cardinality <3:
                self.root = None
                self.root_pc = None
                self.root_note = None
                self.quality = None
                self.bass = None
                self.bass_pc = None
                self.bass_note = None
                self.chord_symbol = None
        elif self.cardinality >2:
                # Chord Quality
                self.quality = chord_quality(chord)
                # Triadic Root
                if self.quality == None:
                        self.root = None
                        self.root_pc = None
                        self.root_note = None
                        self.bass = None
                        self.bass_pc = None
                        self.bass_note = None
                        self.chord_symbol = None
                else:
                        self.root = min(chord) # TODO: Make this work.
                        # Convert Chord Root to Pitch Class.
                        self.root_pc = self.root%12
                        # Convert Chord Root Pitch Class to Note Name.
                        self.root_note = NOTE_KEYS[key][self.root_pc]
                        # Chord Bass
                        self.bass = min(chord)
                        self.bass_pc = min(chord)%12
                        self.bass_note = NOTE_KEYS[key][self.bass_pc]
                # Render Chord Symbol
                        if self.bass != self.root:
                                self.chord_symbol = f"""{self.root_note}
                                                        {self.quality}/
                                                        {self.bass_note}
                                                     """
                        else: self.chord_symbol = f"{self.root_note}{self.quality}"

#def chordsymbol_analysis(filepath, none = True):
#        """ Def.
#            filepath = 
#            none = True/False include no chord entries
#        """
#        chords = [[pitch.midi for pitch in chord.pitches] 
#                   for chord in (music21.converter.parse(filepath)).chordify().
#                   recurse().getElementsByClass('Chord')
#                 ]
#        chord_symbols = [ChordDetect(chord).chord_symbol for chord in chords]
#        if none == True:
#                return chord_symbols
#        elif none == False:
#                try:
#                        while True:
#                                chord_symbols.remove(None)
#                except ValueError:
#                        pass
#                return chord_symbols

# TODO:
# Chord Inversions Gen?
# Add chords automatically
# Bass intervals bad?
###############################################################################
def unique_pc(chord):
        """ Returns tuple of unique pitch classes in a chord.
            chord = list of MIDI or pitch class numbers representing a chord
        """
        return set([note%12 for note in chord])

# Generate sets for all major triads
def triad_quality(chord):
    """
    """
    if unique_pc(chord) in maj:
        return 'maj' 
    elif unique_pc(chord) in min:
        return 'min'
    elif unique_pc(chord) in aug:
        return 'aug'
    elif unique_pc(chord) in dim:
        return 'dim'
"""
test_dict = {
             tuple([{(pitch + pc)%12 for pitch in [0,4,7]} for pc in range (0,12)]): 'maj',
             tuple([{(pitch + pc)%12 for pitch in [0,3,7]} for pc in range (0,12)]): 'min',
             tuple([{(pitch + pc)%12 for pitch in [0,4,8]} for pc in range (0,12)]): 'aug',
             tuple([{(pitch + pc)%12 for pitch in [0,3,6]} for pc in range (0,12)]): 'dim'
            }
"""
###############################################################################
def salami(midi_file, direct: bool = False):
    """
    """
    if not direct:
        midi = MidiFile(midi_file)
    else:
        midi = midi_file
    slices = []
    current_chord = set()
    current_time = 0
    start_time = 0
    
    for i, track in enumerate(midi.tracks):
        for msg in midi.tracks[i]:
            current_time += msg.time
            if current_time == start_time:
                pass
            elif slices and slices[-1][0] == current_chord:
                pass
            elif not current_chord:
                pass
            else:
                slices.append([sorted(list(current_chord)),
                               (current_time - start_time) / midi.ticks_per_beat])
            start_time = current_time
            # If no time has passed, just add it or remove it.
            if msg.time == 0:
                if msg.type == 'note_on' and msg.velocity > 0:
                    current_chord.add(msg.note)
                elif msg.type == 'note_off' or msg.type == "note_on" and msg.velocity == 0:
                    current_chord.discard(msg.note)
                else:
                    print("Unhandled MIDI message:", msg)
                    continue
            else:
                if msg.type == 'note_on':
                    current_chord.add(msg.note)
                elif msg.type == 'note_off':
                    current_chord.discard(msg.note)
                else:
                    print("Unhandled MIDI message:", msg)
                    continue
    return slices

###############################################################################
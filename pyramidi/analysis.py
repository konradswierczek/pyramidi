"""


"""

###############################################################################
# Built-in Imports
from itertools import combinations
# Third Party Imports
from mido import MidiFile, tempo2bpm, MidiTrack
# Local Imports
from pyramidi import get_notes

###############################################################################
def get_pcd(midi: MidiFile):
    """Compute a pitch-class distribution.

    Arguments:
    midi (MidiFile) -- A mido MidiFile

    Returns:
    dictionary -- a pitch class distribution (key = pitch class, value = total ticks)

    """
    # TODO: Add velocity weighting
    # TODO: Add parncutt/eerola thing?
    # TODO: Add normalized?
    pcd = dict.fromkeys(range(0,12), 0)
    notes = get_notes(midi)
    for note in notes:
        pc = note[0]%12
        pcd[pc] = pcd[pc] + note[1]
    return pcd

###############################################################################
def get_pc(chord):
        """Get unique pitch classes.

        Arguments:
        chord (list) -- MIDI or pitch classes

        Returns:
        set -- Unique pitch classes
        
        """
        if not isinstance(chord, list):
                raise TypeError(
                        "Must be list of MIDI or pitch class numbers."
                )
        return set([note % 12 for note in chord])

###############################################################################
def get_ambitus(midi: MidiFile):
    """Get the lowest and highest pitch.

    Arguments:
    midi (MidiFIle) -- A mido MidiFile.

    Returns:
    tuple -- lowest and highest MIDI number.

    """
    note_list = []
    for track in midi.tracks:
        for msg in track:
            if msg.type == "note_on":
                note_list.append(msg.note)
    return min(note_list), max(note_list)

###############################################################################
def get_intervals(chord):
        """All interval classes of a choord

        Arguments:
        chord (list) -- MIDI numbers or pitch classes

        Returns:
        list -- interval classes
        """
        # Get all intervals
        combos = list(combinations(get_pc(chord), 2))
        intervals = [abs(pitch[0]- pitch[1])%12 for pitch in combos]
        return intervals

###############################################################################
def interval_vector(chord):
        """Interval Vector of a chord after Forte 1973.

        Arguments:
        chord (list) -- MIDI numbers or pitch classes

        Returns:
        list -- interval vector

        """
        intervals = get_intervals(chord)
        for ind,interval in enumerate(intervals):
                if interval > 6:
                        intervals[ind] = 12 - intervals[ind]
        interval_vector = [0 for i in range(6)]
        for interval in intervals:
                interval_vector[interval-1] = interval_vector[interval-1] + 1
        return interval_vector

###############################################################################
def bass_intervals(chord: list):
        """Semitone distances between lowest note in a chord.
        
        Arguments:
        chord (list) -- list of MIDI or pitch class numbers representing a chord

        Returns:
        tuple -- interval classes from bass note

        """
        int = [abs(chord[0]-chord[note])%12 for note in range(1,len(chord))]
        if 0 in int:
                int.remove(0)
                return tuple(int)
        else: 
                return tuple(int)

###############################################################################
def identify_chordQuality(chord):
        """
        """
        pass

###############################################################################
def identify_chord(chord):
        """
        """
        pass

###############################################################################



# WIP STUFF
# Constants
__all__ = []
#maj = tuple([{(pitch + pc)%12 for pitch in [0,4,7]} for pc in range (0,12)])
#min = tuple([{(pitch + pc)%12 for pitch in [0,3,7]} for pc in range (0,12)])
#aug = tuple([{(pitch + pc)%12 for pitch in [0,4,8]} for pc in range (0,12)])
#dim = tuple([{(pitch + pc)%12 for pitch in [0,3,6]} for pc in range (0,12)])
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
# NOT TESTED IN BETA

# NOT TESTED IN BETA
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

###############################################################################
# NOT TESTED IN BETA
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
# NOT TESTED IN BETA
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
# NOT TESTED IN BETA
def beat_density(midi_file: str = 'tests/test.mid'):
    midi = midi_file
    ticks = int(second2tick(midi.length, midi.ticks_per_beat, get_tempo(midi)))
    beats = int(ticks / midi.ticks_per_beat)
    slices = salami(midi)
    return len(slices) / beats

###############################################################################
# NOT TESTED IN BETA
def onset_rate(midiFile, time_unit: str = "beat", direct: bool = False):
    """
    """
    if not direct:
        midi = MidiFile(midiFile)
    else:
        midi = midiFile
    tpb = midi.ticks_per_beat
    tempo = [msg.tempo for msg in midi if msg.type == "set_tempo"][0]
    length = int(second2tick(midi.length, tpb, tempo))
    onsets = len(salami(midiFile, direct = direct))
    if time_unit == "beat":
        time_unit = length / tpb
    elif time_unit == "length":
        time_unit = midi.length
    else:
        print("error")
    return onsets / time_unit

###############################################################################

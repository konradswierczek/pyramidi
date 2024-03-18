"""Pitch Salience Algorithm based on Parncutt 1988,1993
    Implemented by Konrad Swierczek and Karen Chan 2022
    Digital Music Lab, McMaster University
"""
###############################################################################
# Constants
__all__ = ['PitchSalience']
WEIGHTS88 = [1, 0, 0.2, 0.1, 0.33, 0, 0, 0.5, 0, 0, 0.25, 0]
WEIGHTS93 = [10, 0, 1, 0, 3, 0, 0, 5, 0, 0, 2, 0]
###############################################################################
class PitchSalience:
    """
    """
    def __init__ (self, chord, weights = 93):
        """ Chord = list of MIDI numbers
            weights = 
            returns
        """
        self.chord = chord
        if weights == 88:
            self.weights = WEIGHTS88
        else: 
            self.weights = WEIGHTS93
        chord_pc =(note%12 for note in self.chord)
        pc_chord = [0 for i in range(12)]
        for note in chord_pc:
            pc_chord[note] = 1
        weight_sums = []
        for pc in range(0,12):
            pc_index = [i%12 for i in range(pc, pc+11)]
            weight_sums.append(sum(list(pc_chord[ind] * 
                                        weight for weight, ind in \
                                            zip(self.weights,pc_index))))
        rasums = [pc/max(weight_sums) for pc in weight_sums]
        self.ra = round(sum(rasums)**0.5,3)
        self.ps = [round((1 / self.ra) * pc, 3) for pc in rasums]
        if len([index for index, value in enumerate(self.ps) if 
                value == max(self.ps)]) > 1:
            self.root_pc = None
            self.root = None
        else:
            self.root_pc = self.ps.index(max(self.ps))
            self.rootmatcher = {note%12:[note] for note in chord}
            #append MIDI notes to list in values of rootmatcher
            self.root = self.rootmatcher[self.root_pc][0]
            # Remove bracket from print
            #will return higher of roots
            #must return LOWER of the all root options, or both

###############################################################################
# TEST THE PARSE MODULE:
from mido import MidiFile
from pyramidi.parse import *
midi = MidiFile("tests/test.mid")
print(get_total_ticks(midi) == 34561)
length_1 = get_measure_length(960, (4, 4))
print(length_1 == 3840)
midi = collapse_tracks(midi)
length_8 = get_ticks_mm(midi)
midi = cut_midi(midi, length_8)
print(get_total_ticks(midi) ==length_1 * 8 )

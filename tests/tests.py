from mido import MidiFile
from pyramidi import *

midi = MidiFile("tests/test.mid")

ts = get_timeSignature(midi)
total_ticks = get_totalTicks(midi)
tempo = get_tempo(midi)
eight_measures = get_ticks_mm(midi, 8)
# collapse_tracks
# filter_msgs
# cut_midi
# find_msgType
print(eight_measures) # BAD

all_keyboard_numbers = [midi2keyboard(i) for i in range(0, 128)]

print(
    transform.change_articulation(midi)
)

print(
    transform.change_tempo(midi)
)

print(
    transform.change_pitchHeight(midi)
)

print(
    transform.change_velocity(midi)
)


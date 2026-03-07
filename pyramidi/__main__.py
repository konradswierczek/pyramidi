"""
python -m pyramidi

Demonstrates the full pyramidi MVP workflow.
"""
from pyramidi import (
    PyraMIDIFile,
    # SetVelocity,
    # TransformTempo,
    # SetArticulation,
    # SetTransposition,
    # change_midi,
)
midi = PyraMIDIFile("tests\\test.mid", cut_measures = 8)


# transformation_vector = [
#     SetVelocity(120),
#     TransformTempo(1.25),
#     SetArticulation(0.75),
#     SetTransposition(2),
# ]

# new_midi = change_midi(transformation_vector, midi)
# print("Output:", new_midi)
#TODO complete transformations
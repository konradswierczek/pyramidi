"""
python -m pyramidi

Demonstrates pyramidi Change workflow.
"""

from pathlib import Path
import argparse

from pyramidi import PyraMIDIFile
from pyramidi.change import *


def main():
    parser = argparse.ArgumentParser(description="Run the PyraMIDI Change demo.")
    parser.add_argument(
        "midi_path",
        nargs="?",
        default=Path("tests") / "test.mid",
        type=Path,
        help="Path to MIDI file (default: tests/test.mid)",
    )

    args = parser.parse_args()

    midi = PyraMIDIFile(args.midi_path, cut_measures=8)

    change_vector = [
        SetVelocity(120),
        TransformTempo(1.25),
        TransformArticulation(0.75),
        TransformPitch(2),
    ]

    new_midi = change_midi(change_vector, midi)

    print("Input:", args.midi_path)
    print("Output:", new_midi)


if __name__ == "__main__":
    main()

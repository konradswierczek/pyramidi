"""
A CLI tool for transforming MIID files.s
"""
# TODO: Add option for cutting MIDI beforehand.

###############################################################################
# Built-in Imports
import inspect
from argparse import ArgumentParser
# Third Party Imports
from mido import MidiFile
# Local Imports
from pyramidi.parse import collapse_tracks, cut_midi
from pyramidi.transform import *

###############################################################################
def discover_transforms():
    """Discover available transform functions by name."""
    transforms = {}
    for name, obj in globals().items():
        if callable(obj) and name.startswith("change_"):
            transforms[name] = obj
    return transforms

###############################################################################
def parse_kwargs(argstr: str) -> dict:
    """Parse key=value pairs into kwargs."""
    kwargs = {}
    if not argstr:
        return kwargs
    for pair in argstr.split(","):
        key, value = pair.split("=")
        if "." in value:
            value = float(value)
        else:
            try:
                value = int(value)
            except ValueError:
                pass
        kwargs[key] = value
    return kwargs

###############################################################################
def main():
    """CLI entrypoint for transform-midi."""
    parser = ArgumentParser(
        description = "Apply ordered transformations to a MIDI file."
    )

    parser.add_argument(
        "-i", "--input-file",
        help = "Input MIDI file (type 0 assumed)."
    )

    parser.add_argument(
        "-o", "--output-file",
        help = "Output MIDI file."
    )

    parser.add_argument(
        "-a", "--apply",
        action = "append",
        default = [],
        metavar = "TRANSFORM[:arg=value,...]",
        help = "Apply a transformation."
    )

    parser.add_argument(
        "-l", "--list-transforms",
        action = "store_true",
        help = "List available transformations and exit."
    )

    args = parser.parse_args()

    # Process apply arguments into transforms.
    transforms = discover_transforms()
    if args.list_transforms:
        print("Available transformations:")
        for name in sorted(transforms):
            fn = transforms[name]
            sig = inspect.signature(fn)
            print(f"    {name}{sig}")
        return

    # Load MIDI.
    midi = MidiFile(args.input_file)
    midi = collapse_tracks(midi)
    pipeline = TransformMidi(midi)

    # Build pipeline.
    for step in args.apply:
        if ":" in step:
            name, argstr = step.split(":", 1)
            kwargs = parse_kwargs(argstr)
        else:
            name = step
            kwargs = {}

        if name not in transforms:
            raise ValueError(f"Unknown transform: {name}")

        pipeline.add(transforms[name], **kwargs)

    # Render and save.
    result = pipeline.render()
    result.save(args.output_file)

###############################################################################
if __name__ == "__main__":
    main()

###############################################################################

"""
A CLI tool for altering MIDI files.

Example:

change-midi -i in.mid -o out.mid \
  -a SetVelocity:velocity=100 \
  -a TransformTempo:tempo_ratio=1.25 \
  -a TransformPitch:amount=2
"""

###############################################################################
# Built-in Imports
import inspect
from argparse import ArgumentParser

# Local Imports
from pyramidi import PyraMIDIFile
from pyramidi.change import *
from pyramidi.change import ChangeMIDI

###############################################################################
def discover_changes():
    """Discover all subclasses of ChangeMIDI."""
    return {cls.__name__: cls for cls in ChangeMIDI.__subclasses__()}

def parse_apply_spec(spec: str):
    """Parse TRANSFORM[:arg=value,...]"""
    if ":" in spec:
        name, argstr = spec.split(":", 1)
        kwargs = parse_kwargs(argstr)
    else:
        name = spec
        kwargs = {}

    return name, kwargs

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
        help = "Input MIDI file."
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
    change_classes = discover_changes()
    if args.list_transforms:

        print("Available Changes:\n")

        for name, cls in discover_changes().items():

            sig = inspect.signature(cls.__init__)
            params = [
                str(p) for p in sig.parameters.values()
                if p.name != "self"
            ]

            print(f"{name}({', '.join(params)})")

        return

    # Load MIDI.
    # TODO: Check if MIDI is type 0 and exit if yes
    midi = PyraMIDIFile(args.input_file)
    change_vector = []

    for spec in args.apply:

        name, kwargs = parse_apply_spec(spec)

        if name not in change_classes:
            raise ValueError(
                f"Unknown transform '{name}'. "
                f"Use --list-transforms to see available options."
            )

        cls = change_classes[name]

        try:
            change = cls(**kwargs)
        except TypeError as e:
            raise ValueError(
                f"Invalid arguments for {name}: {kwargs}"
            ) from e

        change_vector.append(change)

    # Render and save.
    result = change_midi(change_vector, midi)
    result.save(args.output_file)

###############################################################################
if __name__ == "__main__":
    main()

###############################################################################

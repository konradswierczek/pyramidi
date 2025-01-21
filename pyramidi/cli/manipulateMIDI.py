"""Manipulate a MIDI file from the command line



    main() is the CLI entrypoint function.

    Author: Konrad Swierczek (swierckj@mcmaster.ca)
"""

# ============================================================================ #
# Built-in Imports
from argparse import ArgumentParser
# Local Imports
from pyramidi.manipulate import ManipulateMIDI

# ============================================================================ #
def main():
    """
        Command Line Interface Entry Point Function for
        pyramidi.cli.manipulateMIDI.
    """
    # ======================================================================== #
    # Define the CLI parser.
    parser = ArgumentParser(
        description = "Manipulate a midi file."
    )

    # Input MIDI filepath
    parser.add_argument(
        "--input",
        type = str,
        help = "A file path to a midi file for manipulating."
    )

    # Set global MIDI velocity.
    parser.add_argument(
        "--velocity",
        type = int,
        help = "A file path to a midi file for manipulating."
    )

    # Set global MIDI semitone transposition.
    parser.add_argument(
        "--semitones",
        type = int,
        help = "A file path to a midi file for manipulating."
    )

    # Set the global MIDI tempo.
    parser.add_argument(
        "--tempo",
        type = float,
        help = "A file path to a midi file for manipulating."
    )

    # Set the global MIDI articulation 
    # TODO: Add this functionality.
    parser.add_argument(
        "--articulation",
        type = float,
        help = "A file path to a midi file for manipulating."
    )

    # Specify a filepath to output manipulated MIDI file.
    parser.add_argument(
        "--output",
        type = str,
        help = "A file path to output the midi file."
    )

    args = parser.parse_args()

    # ======================================================================== #
    # TODO: Add checks for arguments.

    function_args = {}
    if args.velocity is not None:
        function_args["velocity"] = args.velocity
    if args.tempo is not None:
        function_args["tempo"] = args.tempo
    if args.semitones is not None:
        function_args["semitones"] = args.semitones
    if args.articulation is not None:
        function_args["articulation"] = args.articulation

    # Manipulate MIDI file and output new MIDI file.
    ManipulateMIDI(
        midi_file = args.input,
        output_file = args.output
    ).qwik(**function_args)

# =========================================================================== #
# Execute when the module is not initialized from an import statement.
if __name__ == "__main__":
    main()

# =========================================================================== #
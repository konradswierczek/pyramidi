"""
Render `PyraMIDIFile` objects to audio.

This module provides tools for synthesizing MIDI data into audio files using
FluidSynth. It converts a `PyraMIDIFile` into a temporary MIDI file and renders
it to audio using a specified SoundFont.

Rendering is useful when evaluating MIDI transformations, generating audio
datasets, or preparing stimuli for perceptual experiments.

Classes:
- `SynthesizeAudio`  
    Render a `PyraMIDIFile` to audio using FluidSynth.

Example:
    ```
    from pyramidi import (
        PyraMIDIFile,
        SynthesizeAudio,
        ApplyCompression,
        NormalizeLoudness,
        change_audio
    )
    from os import remove

    midi = PyraMIDIFile("tests/test.mid")
    renderer = SynthesizeAudio()

    wav = renderer.render(midi)
    ```

Notes:
FluidSynth must be installed and available on the system path.

Install with:

    Ubuntu: sudo apt install fluidsynth  
    Mac:    brew install fluidsynth  
    Conda:  conda install -c conda-forge fluidsynth

SoundFonts (`.sf2` files) define the instrument timbres used during synthesis.
If no SoundFont is specified, FluidSynth will attempt to use its system default.
"""
# TODO: Add other fluidsynth params

# =========================================================================== #
from pathlib import Path
from tempfile import NamedTemporaryFile
from subprocess import run, DEVNULL
from os.path import exists
from shutil import which
from os import remove

from .. import PyraMIDIFile

__all__ = ["SynthesizeAudio"]

# =========================================================================== #
def _check_fluidsynth():
    if which("fluidsynth") is None:
        raise RuntimeError(
            "FluidSynth is required for audio rendering but was not found.\n"
            "Install it with:\n"
            "  Ubuntu: sudo apt install fluidsynth\n"
            "  Mac:    brew install fluidsynth\n"
            "  Conda:  conda install -c conda-forge fluidsynth"
        )

# =========================================================================== #
def prepare_tempfile(output_path: str | None = None, suffix: str = ".wav") -> str:
    """Create a temporary file path."""
    if output_path is None:
        with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            return tmp.name
    return output_path

# =========================================================================== #
class SynthesizeAudio:
    """Render PyraMIDIFile objects to audio using FluidSynth."""
    def __init__(self, soundfont: str | None = None):
        """Instantiate and validate a soundfont.
        Arguments:
        soundfont (str | None) -- Path to a .sf2 soundfont file. If None, FluidSynth's default soundfont will be used.
        """
        if soundfont is not None:
            if not exists(soundfont):
                raise FileNotFoundError(f"Soundfont not found: {soundfont}")

            if not soundfont.lower().endswith(".sf2"):
                raise ValueError("Soundfont must be an .sf2 file")

        self.soundfont = soundfont

    def render(
        self,
        midi: PyraMIDIFile,
        output_path: str | None = None,
        silent: bool = True
    ) -> str:
        """
        
        Arguments:
        midi (PyraMIDIFile) -- MIDI object to render.
        output_path (str | None) -- Path to render audio file to.
        silent (bool) -- Suppress fluidsynth output?
        """

        _check_fluidsynth()

        if not isinstance(midi, PyraMIDIFile):
            raise TypeError("midi must be a PyraMIDIFile")

        kwargs = {}
        if silent:
            kwargs["stdout"] = DEVNULL
            kwargs["stderr"] = DEVNULL

        # Prepare output wav.
        output_path = prepare_tempfile(
            output_path,
            ".wav"
        )

        # Write temporary MIDI.
        with NamedTemporaryFile(
            suffix=".mid",
            delete=False
        ) as temp_midi:
            midi_path = temp_midi.name
        midi.save(midi_path)

        # Build FluidSynth command.
        cmd = [
            "fluidsynth",
            "-ni",
        ]

        if self.soundfont is not None:
            cmd.append(self.soundfont)
        else:
            cmd.append("")  # llow default sf2.

        cmd.extend([
            midi_path,
            "-F",
            output_path,
            "-C", "no",
            "-R", "off",
        ])

        try:
            run(cmd, check=True, **kwargs)
        finally:
            # Clean up temporary MIDI file.
            remove(midi_path)
        
        return output_path

    def to_spec(self):
        """Specify the generation.

        Returns:
        Dict[str, Any] -- A dictionary of all information needed to reproduce an instance of the SynthesizeAudio class, including the class name.
        """
        return {
            "type": self.__class__.__name__,
            "soundfont": self.soundfont
        }

    def label(self) -> str:
        if self.soundfont is None:
            return "sf(default)"
        return f"sf({Path(self.soundfont).stem})"

# =========================================================================== #

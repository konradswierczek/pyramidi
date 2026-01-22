"""

Functions
- prepare_tempfile
- fluidsynth
- ffmpeg_reverb
- ffmpeg_compress
- SpecifySoundfont
"""
# TODO: Sort out the soundfont range issue.

# =========================================================================== #
# Built-in Imports
from os.path import basename, exists
from os import remove
from shutil import move
from subprocess import run, DEVNULL
from tempfile import NamedTemporaryFile

__all__ = ["render_audio", "render_reverb", "render_compression", "SpecifySoundfont", "RenderAudio"]

# =========================================================================== #
def prepare_tempfile(output_path: str = None, suffix: str = ".wav") -> str:
    """Create a temporary file path.

    Arguments:
    output_path (str) -- Default to None.
    suffix (str) -- A file extension for the temporary file.

    Returns:
    str: -- The output filepath.

    """
    if output_path is None:
        temp_file = NamedTemporaryFile(
            suffix = suffix,
            delete = False
        )
        output_path = temp_file.name
        temp_file.close()

    return output_path

# =========================================================================== #
def render_audio(
    midi_file: str,
    soundfont: str = "",
    output_path: str = None,
    silent: bool = False
) -> str:
    """
    Converts a MIDI file to an audio file using FluidSynth.

    Arguments:
    midi_file (str) -- Path to the input MIDI file.
    soundfont (str) -- Path to the soundfont file.
    output_path (str, optional): Path to the output audio file. Defaults to a temporary file.

    Returns:
    str: The file path of the generated audio file.
    """
    kwargs = {}
    if silent:
        kwargs["stdout"] = DEVNULL
        kwargs["stderr"] = DEVNULL

    # Prepare the output path.
    output_path = prepare_tempfile(output_path, ".wav")

    run([
        'fluidsynth',
        '-ni',
        soundfont,
        midi_file,
        '-F',
        output_path,
        '-C', 'no',
        '-R', 'off'
    ], check=True, **kwargs)

    return output_path

# =========================================================================== #
def render_reverb(
    audio_file: str,
    ir_file: str,
    output_path: str = None,
    dry: float = 1.0,
    wet: float = 4.0,
    silent: bool = False
) -> str:

    kwargs = {}
    if silent:
        kwargs["stdout"] = DEVNULL
        kwargs["stderr"] = DEVNULL

    output_path = prepare_tempfile(output_path, ".wav")

    filter_complex = (
        "[0:a]asplit=2[dry][in];"
        "[in][1:a]afir[wet];"
        f"[dry][wet]amix=inputs=2:weights={dry} {wet}:normalize=0"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i", audio_file,
        "-i", ir_file,
        "-filter_complex", filter_complex,
        output_path
    ]

    run(command, check=True, **kwargs)
    return output_path

# =========================================================================== #
def render_compression(
    audio_file: str,
    output_path: str = None,
    sr: int = None,
    cbr_bitrate: int = None,
    vbr_quality: int = None,
    silent: bool = False
) -> str:
    """Re-encode a single audio file with specified compression settings.

    Arguments:
    audio_file (str) -- Path to the input audio file.
    output_path (str --) Path to store the compressed file. If None, a temporary path is created and returned.
    sr (int) -- Sample rate for compression (optional, e.g., 22050 or 44100 Hz).
    cbr_bitrate (int) -- Bitrate for CBR compression (optional, e.g., 128 for 128kbps).
    vbr_quality (int) -- Quality setting for VBR compression (optional, e.g., 2 for high quality, 6 for lower quality).

    Returns
    str -- Path to the compressed file.
    """

    kwargs = {}
    if silent:
        kwargs["stdout"] = DEVNULL
        kwargs["stderr"] = DEVNULL

    output_path = prepare_tempfile(output_path, ".mp3")

    base_filename = basename(audio_file).rsplit('_', 1)[0]

    if cbr_bitrate and sr:
        # Constant Bitrate (CBR) Compression.
        run([
            'ffmpeg',
            '-y',
            '-i', audio_file,
            '-ar', str(sr),
            '-b:a', f'{cbr_bitrate}k',
            output_path
        ], check=True, **kwargs)
    elif vbr_quality is not None:
        # Variable Bitrate (VBR) Compression with optional sample rate.
        command = [
            'ffmpeg',
            "-y",
            '-i', audio_file,
            '-q:a', str(vbr_quality)
        ]
        if sr:
            command.extend(['-ar', str(sr)])
        command.append(output_path)
        run(command, check=True, **kwargs)

    return output_path

# =========================================================================== #
class SpecifySoundfont:
    """
    """
    def __init__(self, soundfont_file: str):
        pass

# =========================================================================== #
class RenderAudio:
    def __init__(self, input_path: str):
        self.input_path = input_path
        self.steps = []

    def add(self, render_fn, **kwargs):
        self.steps.append((render_fn, kwargs))
        return self

    def run(self, output_file: str, silent: bool = False) -> str:
        current = self.input_path
        generated = []

        for fn, kwargs in self.steps:
            # Inject silent into each render step.
            if "silent" in fn.__code__.co_varnames:
                kwargs["silent"] = silent

            next_file = fn(current, **kwargs)

            # Track generated files.
            if next_file != current and current != self.input_path:
                generated.append(current)

            current = next_file

        # Move final output into place.
        if current != output_file:
            move(current, output_file)

        # Cleanup intermediates.
        for f in generated:
            if exists(f) and f != output_file:
                remove(f)

        return output_file

# =========================================================================== #

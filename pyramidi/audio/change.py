"""
Procedurally change audio files.

Example:
    ```
    from pyramidi. import *

    renderer = RenderAudio("piano.sf2")

    wav = renderer.render(midi)

    changes = [
        ApplyReverb("hall_ir.wav"),
        ApplyCompression(vbr_quality=4),
        SetLoudness(-14)
    ]

    final = change_audio(changes, wav)
    ```

Change Classes:
    - `ApplyReverb`
    - `ApplyCompression`
    - `SetLoudness`

Use Abstract Class `ChangeAudio` to create new changes.
"""
# TODO: Don't delete first file in `change_audio`
# TODO: Check docstrings
# TODO: Clean up example, add module docstring desc
# TODO: ApplyCompression needs better logic to avoid empty instance
# TODO: Validation for all change inputs
# TODO: Is silent in the right place???
# TODO: Double check reverb code
# TODO: Run tests
# TODO: Fix package level import in init

# =========================================================================== #
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from subprocess import run, DEVNULL
from os import remove
from os.path import basename
from shutil import which

from .synthesize import prepare_tempfile

# =========================================================================== #
def _check_ffmpeg():
    if which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg is required for audio transformations but was not found.\n"
            "Install it with:\n"
            "  Ubuntu: sudo apt install ffmpeg\n"
            "  Mac:    brew install ffmpeg\n"
            "  Conda:  conda install -c conda-forge ffmpeg"
        )

# =========================================================================== #
class ChangeAudio(ABC):
    """
    """
    @abstractmethod
    def change(self, audio_file: str, output_path: str | None = None) -> str:
        """Change an audio file.

        Arguments:
        audio_file (str) -- Path to the input audio file.
        output_path (str) -- Path to store the compressed file. If None, a temporary path is created and returned.

        Returns:
        str -- Path to changed audio file.

        """

    def __call__(self, audio_file: str, output_path: str | None = None) -> str:
        """Run the change method on class call.

        Returns:
        str -- Path to changed audio file.

        """
        return self.change(audio_file, output_path)

    @abstractmethod
    def to_spec(self) -> Dict[str, Any]:
        """Specify the change.

        Returns:
        Dict[str, Any] -- A dictionary of all information needed to reproduce an instance of the Change class, including the class name.
        """

# =========================================================================== #
def change_audio(change_vector: List[ChangeAudio], audio_file: str):
    """Perform a pipeline of ChangeAudio to an audio file."""

    current = audio_file
    generated = []

    for transformation in change_vector:

        if not isinstance(transformation, ChangeAudio):
            raise TypeError("All elements must be ChangeAudio objects")

        next_file = transformation(current)

        if next_file != current:
            generated.append(current)

        current = next_file

    for f in generated:
        try:
            remove(f)
        except OSError:
            pass

    return current

# =========================================================================== #
class ApplyReverb(ChangeAudio):
    """
    """
    def __init__(self, ir: str, dry: float = 1, wet: float = 4):
        """Instantiate and validate a change.

        Arguments:
        dry (float) --
        wet (float) --
        silent (bool) -- Should standard output of ffmpeg print?

        Returns
        str -- Path to the compressed file.

        """
        self.ir = ir
        self.dry = dry
        self.wet = wet

    def change(self, audio_file: str, output_path: str | None = None, silent: bool = True) -> str:
        _check_ffmpeg()
        kwargs = {}
        if silent:
            kwargs["stdout"] = DEVNULL
            kwargs["stderr"] = DEVNULL
        
        output_path = prepare_tempfile(output_path, ".wav")

        filter_complex = (
            "[0:a]asplit=2[dry][in];"
            "[in][1:a]afir[wet];"
            f"[dry][wet]amix=inputs=2:weights={self.dry} {self.wet}:normalize=0"
        )

        command = [
            "ffmpeg",
            "-y",
            "-i", audio_file,
            "-i", self.ir,
            "-filter_complex", filter_complex,
            output_path
        ]

        run(command, check=True, **kwargs)
        return output_path

    def to_spec(self):
        return {
            "type": self.__class__.__name__,
            "ir": self.ir,
            "dry": self.dry,
            "wet": self.wet
        }

# =========================================================================== #
class ApplyCompression(ChangeAudio):
    """
    """
    def __init__(self, sr: int = None, cbr_bitrate: int = None, vbr_quality: int = None):
        """Instantiate and validate a change.

        Arguments:
        sr (int) -- Sample rate for compression (optional, e.g., 22050 or 44100 Hz).
        cbr_bitrate (int) -- Bitrate for CBR compression (optional, e.g., 128 for 128kbps).
        vbr_quality (int) -- Quality setting for VBR compression (optional, e.g., 2 for high quality, 6 for lower quality).
        silent (bool) -- Should standard output of ffmpeg print?

        Returns
        str -- Path to the compressed file.
        """
        self.sr = sr
        self.cbr_bitrate = cbr_bitrate
        self.vbr_quality = vbr_quality

    def change(self, audio_file: str, output_path: str | None = None, silent: bool = True) -> str:
        _check_ffmpeg()
        kwargs = {}
        if silent:
            kwargs["stdout"] = DEVNULL
            kwargs["stderr"] = DEVNULL

        output_path = prepare_tempfile(output_path, ".mp3")

        if self.cbr_bitrate and self.sr:
            # Constant Bitrate (CBR) Compression.
            run([
                'ffmpeg',
                '-y',
                '-i', audio_file,
                '-ar', str(self.sr),
                '-b:a', f'{self.cbr_bitrate}k',
                output_path
            ], check=True, **kwargs)
        elif self.vbr_quality is not None:
            # Variable Bitrate (VBR) Compression with optional sample rate.
            command = [
                'ffmpeg',
                "-y",
                '-i', audio_file,
                '-q:a', str(self.vbr_quality)
            ]
            if self.sr:
                command.extend(['-ar', str(self.sr)])
            command.append(output_path)
            run(command, check=True, **kwargs)

        return output_path

    def to_spec(self):
        return {
            "type": self.__class__.__name__,
            "sr": self.sr,
            "cbr_bitrate": self.cbr_bitrate,
            "vbr_quality": self.vbr_quality
        }

# =========================================================================== #
class NormalizeLoudness(ChangeAudio):
    """
    """
    def __init__(self, target_lufs: float = -14, lra: float = 11, tp: float = -2,):
        """Instantiate and validate a change.
        Arguments:
        target_lufs (float) -- Target loudness in Loudness Units Full Scale.
        lra (float) -- .
        tp (float) -- Set maximum true peak. Range is -9.0 - +0.0. Default value is -2.0. 
        silent (bool) -- Should standard output of ffmpeg print?

        Returns
        str -- Path to the normalized file.
        """
        self.target_lufs = target_lufs
        self.lra = lra
        self.tp = tp

    def change(self, audio_file: str, output_path: str | None = None, silent: bool = True) -> str:
        _check_ffmpeg()
        kwargs = {}
        if silent:
            kwargs["stdout"] = DEVNULL
            kwargs["stderr"] = DEVNULL

        output_path = prepare_tempfile(output_path, ".wav")

        run(
            [
                "ffmpeg",
                "-y",
                "-i", audio_file,
                "-af", f"loudnorm=I={self.target_lufs}:TP={self.tp}:LRA={self.lra}",
                output_path,
            ],
            check=True,
            **kwargs,
        )

        return output_path

    def to_spec(self):
        return {
            "type": self.__class__.__name__,
            "target_lufs": self.target_lufs,
            "lra": self.lra,
            "tp": self.tp
        }

# =========================================================================== #

"""
Procedurally change audio files.

Alter specific aspects of an audio file, or create a pipeline to change multiple aspects. Uses FFMPEG.

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

    changes = [
        ApplyCompression(vbr_quality=6),
        NormalizeLoudness(-6)
    ]

    final = change_audio(changes, wav)
    print(final)
    remove(wav)
    ```

Change Classes:
    - `ApplyReverb`
    - `ApplyCompression`
    - `NormalizeLoudness`

Use Abstract Class `ChangeAudio` to create new changes.
"""
# TODO: Is silent in the right place???
# TODO: Run tests
# TODO: Change audio takes output path?
# TODO: Only .wav for ir?

# =========================================================================== #
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from subprocess import run, DEVNULL
from os import remove
from os.path import basename, exists
from shutil import which

from .synthesize import prepare_tempfile

__all__ = ["change_audio", "ApplyReverb", "NormalizeLoudness", "ApplyCompression"]

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

        if next_file != current and current != audio_file:
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
    """Apply convolution reverb to an audio file using an impulse response.

    The input audio is split into a *dry* signal (original audio) and a *wet*
    signal (audio convolved with the impulse response). These two signals are
    then mixed using FFmpeg's ``amix`` filter with user-defined weights.

    """
    def __init__(self, ir: str, dry: float = 1, wet: float = 10):
        """Instantiate and validate a change.

        Arguments:
        ir (str) -- Path to an IR .wav file.
        dry (float) -- Weight for original (dry) input audio.
        wet (float) -- Wright for audio applied through impulse response.

        Returns
        str -- Path to the new audio file.

        """
        if not exists(ir):
            raise FileNotFoundError(f"Impulse Response not found: {ir}")

        if not ir.lower().endswith(".wav"):
            raise ValueError("ir must be a .wav file")

        if not isinstance(dry, (int, float)):
            raise TypeError("dry must be numeric.")
        if not isinstance(wet, (int, float)):
            raise TypeError("wet must be numeric.")

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
    """Apply MP3 compression to an audio file using FFmpeg.

    Compression can be performed using either:
    - Constant Bitrate (CBR)
    - Variable Bitrate (VBR)

    Only one compression mode may be specified.

    """

    def __init__(
        self, sr: int | None = None,
        cbr_bitrate: int | None = None,
        vbr_quality: int | None = None
    ):
        """Instantiate and validate a change.

        Arguments:
        sr (int, optional) -- Target sample rate in Hz (e.g., 22050, 44100).
        cbr_bitrate (int, optional) -- Bitrate for constant bitrate compression in kbps (e.g., 128, 192, 320).
        vbr_quality (int, optional) -- Quality level for variable bitrate compression using the LAME VBR scale (0–9), where: 0 = highest quality, 9 = lowest.quality
    
        Returns
        str -- Path to the new audio file.

        """

        # Validate compression mode
        if cbr_bitrate is not None and vbr_quality is not None:
            raise ValueError(
                "Specify either 'cbr_bitrate' or 'vbr_quality', not both."
            )

        if cbr_bitrate is None and vbr_quality is None:
            raise ValueError(
                "One compression mode must be specified: "
                "'cbr_bitrate' (CBR) or 'vbr_quality' (VBR)."
            )

        # Validate sample rate.
        if sr is not None:
            if not isinstance(sr, int) or sr <= 0:
                raise ValueError("sr must be a positive integer sample rate.")

        # Validate CBR bitrate.
        if cbr_bitrate is not None:
            if not isinstance(cbr_bitrate, int) or cbr_bitrate <= 0:
                raise ValueError("cbr_bitrate must be a positive integer (kbps).")

        # Validate VBR quality.
        if vbr_quality is not None:
            if not isinstance(vbr_quality, int) or not (0 <= vbr_quality <= 9):
                raise ValueError("vbr_quality must be an integer between 0 and 9.")

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

        if self.cbr_bitrate is not None:
            # Constant Bitrate (CBR)
            command = [
                "ffmpeg",
                "-y",
                "-i", audio_file,
                "-b:a", f"{self.cbr_bitrate}k"
            ]

            if self.sr:
                command.extend(["-ar", str(self.sr)])

            command.append(output_path)

        else:
            # Variable Bitrate (VBR)
            command = [
                "ffmpeg",
                "-y",
                "-i", audio_file,
                "-q:a", str(self.vbr_quality)
            ]

            if self.sr:
                command.extend(["-ar", str(self.sr)])

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
    Normalize audio loudness using FFmpeg's EBU R128 `loudnorm` filter.

    This transformation adjusts the perceived loudness of an audio file to
    match a target integrated loudness while constraining loudness range and
    true peak levels.

    The normalization is performed using FFmpeg's `loudnorm` filter in
    single-pass dynamic mode.

    """

    def __init__(self, target_lufs: float = -14, lra: float = 11, tp: float = -2):
        """Instantiate and validate a change.

        Arguments:
        target_lufs (float) -- Target integrated loudness in LUFS (Loudness Units relative to Full Scale).
            Valid range: -70.0 to -5.0.
        lra (float) -- Target loudness range (LRA), controlling dynamic variation.
            Valid range: 1.0 to 50.0.
            Lower values compress dynamic range more strongly.
        tp (float) -- Maximum allowed true peak level in dBFS.
            Valid range: -9.0 to 0.0.
            This prevents clipping after loudness normalization.

        Returns
        str -- Path to the new audio file.
        """

        # Validate target loudness.
        if not (-70.0 <= target_lufs <= -5.0):
            raise ValueError(
                "target_lufs must be between -70.0 and -5.0 LUFS."
            )

        # Validate loudness range.
        if not (1.0 <= lra <= 50.0):
            raise ValueError(
                "lra must be between 1.0 and 50.0."
            )

        # Validate true peak.
        if not (-9.0 <= tp <= 0.0):
            raise ValueError(
                "tp must be between -9.0 and 0.0 dBFS."
            )

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
                "-af",
                f"loudnorm=I={self.target_lufs}:TP={self.tp}:LRA={self.lra}",
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
            "tp": self.tp,
        }

# =========================================================================== #

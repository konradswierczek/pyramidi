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

# =========================================================================== #
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from subprocess import run, DEVNULL, PIPE
from os import remove
from os.path import exists, join
from shutil import which
import re
import tempfile
from pathlib import Path

import numpy as np
from soundfile import read, write

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

    @property
    def output_suffix(self) -> str:
        """File extension produced by this change, including the leading dot.

        Defaults to '.wav'. Override in subclasses that produce a different
        format (e.g. ApplyCompression = '.mp3').
        """
        return ".wav"

    @abstractmethod
    def change(self, audio_file: str, output_path: str | None = None) -> str:
        """Change an audio file.

        Arguments:
        audio_file (str) -- Path to the input audio file.
        output_path (str) -- Path to store the changed file. If None, a
            temporary path is created and returned.

        Returns:
        str -- Path to changed audio file.
        """

    def __call__(self, audio_file: str, output_path: str | None = None) -> str:
        return self.change(audio_file, output_path)

    @abstractmethod
    def to_spec(self) -> Dict[str, Any]:
        """Specify the change.

        Returns:
        Dict[str, Any] -- A dictionary of all information needed to reproduce
            an instance of the Change class, including the class name.
        """

    @abstractmethod
    def label(self) -> str:
        """A short human-readable label for this change.

        Used to construct filenames. Should be brief and descriptive enough
        to identify the change at a glance — full reproduction is handled
        by to_spec().

        Examples: 'vbr4', 'lufs-14', 'verb0.5'
        """

# =========================================================================== #
def change_audio(change_vector: List[ChangeAudio], audio_file: str, output_path: str | None = None):
    current = audio_file
    generated = []

    for i, transformation in enumerate(change_vector):
        if not isinstance(transformation, ChangeAudio):
            raise TypeError("All elements must be ChangeAudio objects")

        is_last = (i == len(change_vector) - 1)
        next_file = transformation(current, output_path=output_path if is_last else None)

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
    """Apply convolution reverb using afir + exact peak normalization (-1 dBFS)."""

    def __init__(self, ir: str, target_peak: float = -1):
        if not exists(ir):
            raise FileNotFoundError(f"Impulse Response not found: {ir}")
        if not ir.lower().endswith(".wav"):
            raise ValueError("ir must be a .wav file")
        if not -60 < target_peak < 0:
            raise ValueError("target_peak must be greater than -60 and less than 0.")

        self.ir = ir
        self.target_peak = target_peak

    def _detect_peak(self, audio_file: str) -> float:
        """Replicates: afir,volumedetect"""
        command = [
            "ffmpeg",
            "-i", audio_file,
            "-i", self.ir,
            "-lavfi", "afir,volumedetect",
            "-f", "null",
            "-"
        ]

        result = run(command, stdout=DEVNULL, stderr=PIPE, text=True, check=True)

        match = re.search(r"max_volume:\s*(-?\d+(\.\d+)?)\s*dB", result.stderr)
        if not match:
            raise RuntimeError("Could not parse max_volume from ffmpeg output")

        return float(match.group(1))

    def change(self, audio_file: str, output_path: str | None = None, silent: bool = True) -> str:
        _check_ffmpeg()

        output_path = prepare_tempfile(output_path, self.output_suffix)

        # ------------------------------------------------------------------ #
        # Pass 1: measure peak after convolution
        peak = self._detect_peak(audio_file)
        gain = self.target_peak - peak

        if not silent:
            print(f"Detected peak: {peak}")
            print(f"Applying gain: {gain} dB")

        kwargs = {}
        if silent:
            kwargs["stdout"] = DEVNULL
            kwargs["stderr"] = DEVNULL

        # ------------------------------------------------------------------ #
        # Pass 2: apply convolution again + gain
        command = [
            "ffmpeg", "-y",
            "-i", audio_file,
            "-i", self.ir,
            "-lavfi", f"afir,volume={gain}dB",
            output_path,
        ]

        if not silent:
            print(" ".join(command))

        run(command, check=True, **kwargs)
        return output_path

    def to_spec(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "ir": self.ir,
            "target_db": self.target_peak,
        }

    def label(self) -> str:
        s = str(self.target_peak)
        val = s.replace('-', 'm').replace('.', 'p')
        return f"verb({Path(self.ir).stem})_peak{val}"

# =========================================================================== #
class ApplyCompression(ChangeAudio):
    """Apply MP3 compression to an audio file using FFmpeg."""

    @property
    def output_suffix(self) -> str:
        return ".mp3"

    def __init__(
        self,
        sr: int | None = None,
        cbr_bitrate: int | None = None,
        vbr_quality: int | None = None,
    ):
        """
        Arguments:
        sr (int, optional) -- Target sample rate in Hz (e.g., 22050, 44100).
        cbr_bitrate (int, optional) -- Bitrate for CBR compression in kbps.
        vbr_quality (int, optional) -- Quality level for VBR (0–9, 0 = best).
        """
        if cbr_bitrate is not None and vbr_quality is not None:
            raise ValueError("Specify either 'cbr_bitrate' or 'vbr_quality', not both.")

        if cbr_bitrate is None and vbr_quality is None:
            raise ValueError(
                "One compression mode must be specified: "
                "'cbr_bitrate' (CBR) or 'vbr_quality' (VBR)."
            )

        if sr is not None and (not isinstance(sr, int) or sr <= 0):
            raise ValueError("sr must be a positive integer sample rate.")

        if cbr_bitrate is not None and (not isinstance(cbr_bitrate, int) or cbr_bitrate <= 0):
            raise ValueError("cbr_bitrate must be a positive integer (kbps).")

        if vbr_quality is not None and (not isinstance(vbr_quality, int) or not 0 <= vbr_quality <= 9):
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

        output_path = prepare_tempfile(output_path, self.output_suffix)

        if self.cbr_bitrate is not None:
            command = ["ffmpeg", "-y", "-i", audio_file, "-b:a", f"{self.cbr_bitrate}k"]
        else:
            command = ["ffmpeg", "-y", "-i", audio_file, "-q:a", str(self.vbr_quality)]

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
            "vbr_quality": self.vbr_quality,
        }

    def label(self) -> str:
        if self.cbr_bitrate is not None:
            return f"cbr{self.cbr_bitrate}k"
        return f"vbr{self.vbr_quality}"

# =========================================================================== #
class NormalizeLoudness(ChangeAudio):
    """Normalize audio loudness using FFmpeg's EBU R128 loudnorm filter."""

    def __init__(self, target_lufs: float = -14, lra: float = 11, tp: float = -2):
        """
        Arguments:
        target_lufs (float) -- Target integrated loudness in LUFS. Range: -70.0 to -5.0.
        lra (float) -- Target loudness range. Range: 1.0 to 50.0.
        tp (float) -- Maximum true peak level in dBFS. Range: -9.0 to 0.0.
        """
        if not (-70.0 <= target_lufs <= -5.0):
            raise ValueError("target_lufs must be between -70.0 and -5.0 LUFS.")

        if not (1.0 <= lra <= 50.0):
            raise ValueError("lra must be between 1.0 and 50.0.")

        if not (-9.0 <= tp <= 0.0):
            raise ValueError("tp must be between -9.0 and 0.0 dBFS.")

        self.target_lufs = target_lufs
        self.lra = lra
        self.tp = tp

    def change(self, audio_file: str, output_path: str | None = None, silent: bool = True) -> str:
        _check_ffmpeg()

        kwargs = {}
        if silent:
            kwargs["stdout"] = DEVNULL
            kwargs["stderr"] = DEVNULL

        output_path = prepare_tempfile(output_path, self.output_suffix)

        run(
            [
                "ffmpeg", "-y",
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
            "tp": self.tp,
        }

    def label(self) -> str:
        return f"lufs{self.target_lufs}"

# =========================================================================== #
# NOTE: BAD!!!! NOISE!!!!
class NormalizePeak(ChangeAudio):
    """Normalize audio to a target peak level using a two-pass FFmpeg workflow."""

    def __init__(self, target_db: float = -1.0):
        """
        Arguments:
        target_db (float) -- Target peak level in dBFS (default: -1.0).
        """
        if not isinstance(target_db, (int, float)):
            raise ValueError("target_db must be a number")

        self.target_db = float(target_db)

    def _detect_peak(self, audio_file: str) -> float:
        """Return max_volume (dBFS) using FFmpeg volumedetect."""
        command = [
            "ffmpeg",
            "-i", audio_file,
            "-af", "volumedetect",
            "-f", "null",
            "-"
        ]

        result = run(command, stdout=DEVNULL, stderr=PIPE, text=True, check=True)

        match = re.search(r"max_volume:\s*(-?\d+(\.\d+)?)\s*dB", result.stderr)
        if not match:
            raise RuntimeError("Could not parse max_volume from ffmpeg output")

        return float(match.group(1))

    def change(self, audio_file: str, output_path: str | None = None, silent: bool = True) -> str:
        _check_ffmpeg()

        output_path = prepare_tempfile(output_path, self.output_suffix)

        kwargs = {}
        if silent:
            kwargs["stdout"] = DEVNULL
            kwargs["stderr"] = DEVNULL

        # ------------------------------------------------------------------ #
        # Pass 1: measure peak
        peak = self._detect_peak(audio_file)

        # Compute gain
        gain = self.target_db - peak

        if not silent:
            print(f"Detected peak: {peak} dB")
            print(f"Applying gain: {gain} dB")

        # ------------------------------------------------------------------ #
        # Pass 2: apply gain
        command = [
            "ffmpeg", "-y",
            "-i", audio_file,
            "-af", f"volume={gain}dB",
            output_path,
        ]

        if not silent:
            print(" ".join(command))

        run(command, check=True, **kwargs)
        return output_path

    def to_spec(self) -> dict:
        return {
            "type": self.__class__.__name__,
            "target_db": self.target_db,
        }

    def label(self) -> str:
        return f"norm_peak{self.target_db}dB"

# =========================================================================== #

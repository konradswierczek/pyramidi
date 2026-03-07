"""
Pyramidi - Minimum Viable Product
======================================

Core Components:
1. PyraMIDIFile            - Main class wrapping mido.MidiFile
2. TransformationFunction  - Abstract base class for transformations
3. Concrete transformations - SetVelocity, TransformTempo, SetArticulation, SetTransposition
4. change_midi             - Applies a transformation_vector to a PyraMIDIFile

Workflow:
    from pyramidi import PyraMIDIFile, change_midi
    from pyramidi import SetVelocity, TransformTempo, SetArticulation, SetTransposition

    midi = PyraMIDIFile("tests/test.mid")

    transformation_vector = [
        SetVelocity(120),
        TransformTempo(1.25),
        SetArticulation(0.75),
        SetTransposition(2),
    ]

    new_midi = change_midi(transformation_vector, midi)
    print(new_midi)
"""

###############################################################################
# Standard Library
from abc import ABC, abstractmethod
from typing import Optional, List
from pathlib import Path

# Third Party
from mido import MidiFile, MidiTrack, Message

# Local
from .parse import collapse_tracks, cut_midi, get_ticks_mm
from .transform import change_transposition, change_velocity, change_tempi_ratio, change_articulation
from .abstract import Slice, slice_salami

###############################################################################
# 1. PyraMIDIFile
###############################################################################

class PyraMIDIFile:
    """
    Main MIDI file class for pyramidi.

    Wraps mido.MidiFile with preprocessing and analysis capabilities.

    Args:
        filepath:     Path to MIDI file.
        collapse:     Merge all tracks into a single Type 0 track. Default: True.
        cut_measures: Truncate to this many measures. Default: None (no cut).

    Example:
        >>> import pyramidi
        >>> midi = pyramidi.PyraMIDIFile("song.mid")
        >>> print(midi)
        PyraMIDIFile(tracks=1, ticks_per_beat=480, type=0)
    """

    def __init__(
        self,
        filepath: Optional[str] = None,
        collapse: bool = True,
        cut_measures: Optional[int] = None,
    ):
        self.filepath = Path(filepath) if filepath else None
        self.midi: Optional[MidiFile] = None

        if filepath:
            self.midi = MidiFile(str(filepath))
            if collapse:
                self.midi = collapse_tracks(self.midi)
            if cut_measures is not None:
                cut_tick = get_ticks_mm(self.midi, n_measures=cut_measures)
                self.midi = cut_midi(self.midi, cut_tick)
        else:
            self.midi = MidiFile(type=0, ticks_per_beat=480)

    # -------------------------------------------------------------------------
    # File I/O
    # -------------------------------------------------------------------------

    def save(self, filepath: Optional[str] = None) -> "PyraMIDIFile":
        """Save MIDI to disk. Uses original filepath if none provided."""
        if filepath is None:
            if self.filepath is None:
                raise ValueError("No filepath specified.")
            filepath = self.filepath
        self.midi.save(str(filepath))
        return self

    def copy(self) -> "PyraMIDIFile":
        """Return a deep copy of this PyraMIDIFile."""
        new = PyraMIDIFile()
        new.midi = MidiFile(type=self.midi.type, ticks_per_beat=self.midi.ticks_per_beat)
        for track in self.midi.tracks:
            new_track = MidiTrack()
            for msg in track:
                new_track.append(msg.copy())
            new.midi.tracks.append(new_track)
        return new

    # -------------------------------------------------------------------------
    # Delegated mido.MidiFile properties
    # -------------------------------------------------------------------------

    @property
    def tracks(self):
        return self.midi.tracks

    @property
    def ticks_per_beat(self) -> int:
        return self.midi.ticks_per_beat

    @property
    def type(self) -> int:
        return self.midi.type

    @property
    def length(self) -> float:
        """Duration in seconds."""
        return self.midi.length

    # -------------------------------------------------------------------------
    # Analysis methods
    # -------------------------------------------------------------------------

    def get_salami_slices(self) -> list[Slice]:
        """
        Return vertical (chordal) slices of the MIDI file.

        Delegates to abstract.slice_salami. Each Slice carries timing context
        (tempo, ticks_per_beat, time_signature) alongside its notes.

        Returns:
            list[Slice] -- one Slice per unique vertical sonority.
        """
        return slice_salami(self.midi)

    # -------------------------------------------------------------------------
    # Dunder methods
    # -------------------------------------------------------------------------

    def __repr__(self) -> str:
        if self.midi is None:
            return "PyraMIDIFile(empty)"
        return (
            f"PyraMIDIFile("
            f"tracks={len(self.midi.tracks)}, "
            f"ticks_per_beat={self.ticks_per_beat}, "
            f"type={self.type})"
        )

    def __str__(self) -> str:
        return self.__repr__()


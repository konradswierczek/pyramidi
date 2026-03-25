"""Synthesize and Change Audio Files

Synthesize `PyraMIDIFile` using fluidsynth, and change existing audio files using ffmpeg. Although this package is mainly focused on MIDI, it made sense to have a generic framework for synthesizing files, and some of the MAPLE Lab's work on procedural transformations makes it convenient to have a 'one-stop-shop'. Also useful for creating stimuli for experiments procedurally.

REQUIRES BOTH ffmpeg AND fluidsynth
"""

from .change import *
from .synthesize import *

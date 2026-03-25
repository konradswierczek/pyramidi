"""
"""

from typing import List, Union

from ..change import ChangeMIDI
from ..audio.change import ChangeAudio, change_audio
from ..audio.synthesize import SynthesizeAudio
from .. import PyraMIDIFile

__all__ = ["MIDI2Audio"]

PipelineItem = Union["ChangeMIDI", "SynthesizeAudio", "ChangeAudio"]

class MIDI2Audio:
    def __init__(self, changes: List[PipelineItem]):
        if not changes:
            raise ValueError("The pipeline cannot be empty.")
        synth_count = 0
        synth_index = None
        first_changeaudio_index = None

        for idx, c in enumerate(changes):
            if not isinstance(c, (ChangeMIDI, SynthesizeAudio, ChangeAudio)):
                raise TypeError(
                    "All elements must be ChangeMIDI, SynthesizeAudio, or ChangeAudio"
                )

            if isinstance(c, SynthesizeAudio):
                synth_count += 1
                synth_index = idx
            elif isinstance(c, ChangeAudio) and first_changeaudio_index is None:
                first_changeaudio_index = idx

        if synth_count != 1:
            raise ValueError("Exactly one SynthesizeAudio instance must be passed.")

        for idx, c in enumerate(changes):
            if isinstance(c, ChangeMIDI) and idx > synth_index:
                raise ValueError("SynthesizeAudio must come after all ChangeMIDI instances.")

        if first_changeaudio_index is not None and synth_index > first_changeaudio_index:
            raise ValueError("SynthesizeAudio must come before any ChangeAudio instances.")

        self.changes = changes

    def apply(self, midi: PyraMIDIFile):
        audio_file = None

        for change in self.changes:
            if isinstance(change, ChangeMIDI):
                midi = change(midi)
                print(type(midi))

            elif isinstance(change, SynthesizeAudio):
                audio_file = change.render(midi)

        # Apply all audio changes using managed pipeline
        audio_changes = [c for c in self.changes if isinstance(c, ChangeAudio)]
        if audio_changes:
            audio_file = change_audio(audio_changes, audio_file)

        return audio_file

    def to_spec(self):
        return [c.to_spec() for c in self.changes]

    def __eq__(self, other):
        if not isinstance(other, MIDI2Audio):
            return False
        # Compare based on list of change specs
        return self.to_spec() == other.to_spec()

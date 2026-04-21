"""
"""
from pathlib import Path
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

    def filename(self, prefix: str | None = None) -> str:
        """A human-readable filename for the output of this pipeline.

        Composed from the labels of all non-SynthesizeAudio steps. The file
        extension is determined by the last ChangeAudio step if present,
        otherwise .wav.

        Arguments:
        prefix (str | None) -- Optional prefix prepended to the filename,
            separated by an underscore. Useful for including the source MIDI
            stem so files remain identifiable if moved out of their folder.

        Examples:
            changer.filename()
            → 'pitch+2.wav'

            changer.filename(prefix="nocturne")
            → 'nocturne_pitch+2.wav'
        """
        labels = [c.label() for c in self.changes]

        audio_changes = [c for c in self.changes if isinstance(c, ChangeAudio)]
        ext = audio_changes[-1].output_suffix if audio_changes else ".wav"

        name = "-".join(labels) + ext
        return f"{prefix}-{name}" if prefix else name

    def apply(self, midi: PyraMIDIFile, output_path: str | None = None) -> str:
        """Apply the pipeline to a PyraMIDIFile.

        Arguments:
        midi (PyraMIDIFile) -- The MIDI file to process.
        output_path (str | None) -- Destination path for the rendered audio.
            If None, a temporary file is created and its path returned.

        Returns:
        str -- Path to the output audio file.
        """
        audio_file = None

        for change in self.changes:
            if isinstance(change, ChangeMIDI):
                midi = change(midi)
            elif isinstance(change, SynthesizeAudio):
                # Pass output_path only if there are no ChangeAudio steps after
                # synthesis — otherwise we render to a temp file and let the
                # audio pipeline write the final output.
                audio_changes = [c for c in self.changes if isinstance(c, ChangeAudio)]
                synth_output = output_path if not audio_changes else None
                audio_file = change.render(midi, output_path=synth_output)

        audio_changes = [c for c in self.changes if isinstance(c, ChangeAudio)]
        if audio_changes:
            audio_file = change_audio(audio_changes, audio_file, output_path=output_path)

        return audio_file

    def to_spec(self):
        return [c.to_spec() for c in self.changes]

    def __eq__(self, other):
        if not isinstance(other, MIDI2Audio):
            return False
        return self.to_spec() == other.to_spec()

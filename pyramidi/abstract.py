"""
Convert MIDI files into mid-level abstractions suitable for analyses.

Functions:
- slice_salami
- slice_bites
"""

###############################################################################
# Built-in Imports
from collections import defaultdict
from dataclasses import dataclass
from typing import Tuple, Literal
# Third Party Imports
from mido import MidiFile

__all__ = ["slice_salami", "slice_bites", "segment_measures", "segment_beats"]

###############################################################################
@dataclass
# NOTE: A flaw here is that the time signature AND possibly tempo doesn't necessarily hold true through an entire event...
class TimedEvent:
    tempo: int
    ticks_per_beat: int
    time_signature: Tuple[int, int]
    start: int
    duration: int

    @property
    def end(self) -> int:
        return self.start + self.duration

    @property
    def duration_beats(self) -> float:
        return self.duration / self.ticks_per_beat

    @property
    def duration_quarters(self) -> float:
        return self.duration_beats

    @property
    def duration_seconds(self) -> float:
        return self.duration_beats * (self.tempo / 1_000_000)

    @property
    def bpm(self) -> float:
        return 60_000_000 / self.tempo

###############################################################################
@dataclass
class Bite(TimedEvent):
    note: int
    velocity: int

    @property
    def pc(self) -> int:
        return self.note % 12

    @property
    def keynum(self) -> int:
        return self.note - 20

###############################################################################  
@dataclass
class Slice(TimedEvent):
    notes: list[int]

    @property
    def pcs(self) -> list[int]:
        return sorted({n % 12 for n in self.notes})

    @property
    def keynum(self) -> int:
        return sorted({n - 20 for n in self.notes})

    @property
    def cardinality(self) -> int:
        return len(self.notes)

###############################################################################
@dataclass
class TimingContext:
    tempo: int
    ticks_per_beat: int
    time_signature: tuple[int, int]

###############################################################################
def slice_salami(midi: MidiFile) -> list[Slice]:
    """Reduce to chords.

    Arguments:
    midi (MidiFile) -- A type 0 mido MidiFile.

    Returns:
        list[Slice] -- slices updated whenever a new note is added.
    """
    # Tracking objects.
    slices = []
    current_chord = set()
    absolute_time = 0

    context = TimingContext(
        tempo = 500000,
        ticks_per_beat = midi.ticks_per_beat,
        time_signature = (4, 4),
    )

    for msg in midi.tracks[0]:  # Type 0 assumed.
        # Advance time.
        absolute_time += msg.time

        # Close slice if chord exists and time has passed.
        if msg.time > 0 and current_chord:
            slices.append(
                Slice(
                    notes=set(current_chord),
                    tempo=context.tempo,
                    ticks_per_beat=context.ticks_per_beat,
                    time_signature=context.time_signature,
                    start=absolute_time - msg.time,
                    duration=msg.time
                )
            )

        # Update timing context if relevant.
        if msg.type == "set_tempo":
            context.tempo = msg.tempo

        if msg.type == "time_signature":
            context.time_signature = (msg.numerator, msg.denominator)

        # Update chord state.
        if msg.type == "note_on" and msg.velocity > 0:
            current_chord.add(msg.note)

        elif msg.type == "note_off" or (
            msg.type == "note_on" and msg.velocity == 0
        ):
            current_chord.discard(msg.note)

    return slices

###############################################################################
def slice_bites(midi: MidiFile) -> list[Bite]:
    """Reduce to single notes.

    Arguments:
    midi (MidiFile) -- A type 0 mido MidiFile.

    Returns:
        list[Bite] -- A bite for each note played.
    """
    # Tracking objects.
    note_events = []
    active_notes = defaultdict(list)

    absolute_time = 0

    context = TimingContext(
        tempo = 500000,
        ticks_per_beat = midi.ticks_per_beat,
        time_signature = (4, 4),
    )

    for track in midi.tracks:
        absolute_time = 0  # Reset for each track (type 0 behavior).
        # TODO: Is this approach better than what I did in slice_salami?

        for msg in track:
            # Advance time.
            absolute_time += msg.time

            # Update timing context.
            if msg.type == "set_tempo":
                context.tempo = msg.tempo

            if msg.type == "time_signature":
                context.time_signature = (msg.numerator, msg.denominator)

            # Capture notes as individual events.
            if msg.type == "note_on" and msg.velocity > 0:
                key = (msg.channel, msg.note)
                active_notes[key].append((absolute_time, msg.velocity))

            elif msg.type in ("note_off", "note_on") and msg.velocity == 0:
                key = (msg.channel, msg.note)

                if active_notes[key]:
                    start, velocity = active_notes[key].pop()
                    duration = absolute_time - start

                    note_events.append(
                        Bite(
                            note = msg.note,
                            velocity = velocity,
                            start = start,
                            duration = duration,
                            tempo = context.tempo,
                            ticks_per_beat = context.ticks_per_beat,
                            time_signature = context.time_signature,
                        )
                    )

    note_events.sort(key = lambda n: n.start)
    return note_events

###############################################################################
@dataclass
class Segment:
    level: Literal["beat", "measure"]
    index: int
    start: int
    duration: int
    slices: list["Slice"]

###############################################################################
def segment_measures(slices: list[Slice]) -> list[Segment]:
    # NOTE: CANNOT HANDLE ANACRUSIS
    ts_num, _ = slices[0].time_signature
    tpq = slices[0].ticks_per_beat
    slice_ticks = slices[0].duration

    slices_per_beat = tpq // slice_ticks
    slices_per_measure = ts_num * slices_per_beat

    segments = []
    for i in range(0, len(slices), slices_per_measure):
        group = slices[i:i + slices_per_measure]
        if not group:
            continue

        measure_idx = i // slices_per_measure
        start = group[0].start
        duration = sum(sl.duration for sl in group)

        segments.append(
            Segment(
                level="measure",
                index=measure_idx,
                start=start,
                duration=duration,
                slices=group
            )
        )

    return segments

###############################################################################
def segment_beats(slices: list[Slice]) -> list[Segment]:
    # NOTE: Technically this segements by equivilant quarter note, which isn't really in the spirit.
    tpb = slices[0].ticks_per_beat

    beats = {}
    for sl in slices:
        beat_idx = sl.start // tpb
        beats.setdefault(beat_idx, []).append(sl)

    segments = []
    for idx, group in sorted(beats.items()):
        start = group[0].start
        duration = sum(sl.duration for sl in group)
        segments.append(
            Segment(
                level="beat",
                index=idx,
                start=start,
                duration=duration,
                slices=group
            )
        )

    return segments

###############################################################################

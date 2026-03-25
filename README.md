# PYraMIDI
A package for processing, manipulating, and analyzing MIDI files using Mido. Primarily designed and tested on MIDI representations of keyboard music. Similar to other tools, most notably the incredibly useful music21, but largely created for some niche work in the Digital Music Lab and the Music Acoustics Perceptual and LEarning Lab at McMaster University. Also notably a way for me to get a bit more comfortable with turning MIDI data into meaningful musical representations.

Install with pip:
``` python
pip install git+https://github.com/konradswierczek/pyramidi.git
```

## Usage
Most use-cases of this package will start with a mido MidiFile:
```
from mido import MidiFile
midi = MidiFile("a_midi_file.mid")
```

> [!NOTE]
> EVERYTHING ELSE IN THE USAGE SECTION IS OUT OF DATE FOR VERSION 2

Generally speaking, this package is designed with type-0 MIDI files in mind. it's a good practice to first reformat your files.:
```
from pyramidi import collapse_tracks
midi = collapse_tracks(midi)
```

Some analysis functions, typically those with the prefix "get_", can accept MidiFile objects directly:
```
from pyramidi.sdc import get_arScore
get_arScore(midi)
```

Other analysis tools require more decision making on the user's part. For instance, the package's implementation of Parncutt's (1988, 1993) pitch salience algorithm will require some extra steps:
```
from pyramidi.models import PitchSalience
slices = slice_salami(midi)
roots = [PitchSalience(chord[0]).root_pc for chord in slices]
```

## Dependencies
This packages makes extensive use of Mido (https://github.com/mido/mido) to facilitate reading and writing MIDI files.

## Roadmap
- Clean up analysis.hutch78
- Adapt change module framework to synthesis
- Intergate abstractions into PyraMIDIFile

- Figure out a policy for imports
- Measure-wise score defined cues
- Add contribution guidelines
- Add cutting for transform-midi cli
- Add option to parse.cut_midi for start tick
- Rework README to reflect new structure
- Build more tests

- Add change_audio cli or midi-audio cli?

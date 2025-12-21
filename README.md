# PYraMIDI
A package for processing, manipulating, and analyzing MIDI files using Mido. Primarily designed and tested on MIDI representations of keyboard music.

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

## Modules
**Core:** Functions for pre-processing, cutting, and extracting basic properties.\
**Analysis:** Functions for statistical analysis of MIDI files.\
**Models:** Perceptual models for analyzing music.\
**Score Defined Cues (sdc):** Automatic extraction after McMaster MAPLE Lab work.\
**Manipulate:** Functions for altering specific properties in MIDI files.

## Dependencies
This packages makes extensive use of Mido (https://github.com/mido/mido) to facilitate reading and writing MIDI files.

## Roadmap
- Clean up models and analysis module
    - Fix and supplement pcd (also move pcd to core module)
- Measure-wise score defined cues
- Add contribution guidelines
- Revist CLI
- Rework a generic class for transforming all available dimensions at once.
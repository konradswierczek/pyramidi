# PYraMIDI

A package for processing, manipulating, and analyzing MIDI files using Mido.

Install with pip:
``` python
pip install git+https://github.com/konradswierczek/pyramidi.git
```

## Modules
### Core

Some core functions for pre-processing MIDI files and extracting properties.

### Analysis

Functions for statistical analysis of MIDI files.

### Models

A number of perceptual models for analyzing music.

### Score Defined Cues (SDC)

Automatic extraction of SDC's after McMaster MAPLE Lab work.

### Manipulate

Functions for changing and exporting MIDI files.

### Tools

Generally not MIDI specific tools used for corpus analysis and synthesis.

## Dependencies

This packages makes extensive use of Mido (https://github.com/mido/mido) to import and export MIDI files.
It also uses Pandas and SciPy for a few functions, but I hope to minimize the amount of dependencies moving forward.
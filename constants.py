import numpy as np

# --- Input Representation Parameters ---

# Number of positions per quarter note for the input representation
DEFAULT_POS_PER_QUARTER = 12

# Velocity bins for MIDI note velocities, ranging from 0 to 128
DEFAULT_VELOCITY_BINS = np.linspace(0, 128, 33, dtype=int)

# Custom duration bins for note durations
DEFAULT_DURATION_BINS = np.sort(np.concatenate([
    np.arange(1, 13),                   # Smallest units up to 1 quarter note
    np.arange(12, 24, 3)[1:],           # 16th notes up to 1 bar
    np.arange(13, 24, 4)[1:],           # Triplets up to 1 bar
    np.arange(24, 48, 6),               # 8th notes up to 2 bars
    np.arange(48, 4 * 48, 12),          # Quarter notes up to 8 bars
    np.arange(4 * 48, 16 * 48 + 1, 24)  # Half notes up to 16 bars
]))

# Tempo bins, ranging from 0 to 240 BPM
DEFAULT_TEMPO_BINS = np.linspace(0, 240, 33, dtype=int)

# Note density bins, ranging from 0 to 12
DEFAULT_NOTE_DENSITY_BINS = np.linspace(0, 12, 33)

# Mean velocity bins, ranging from 0 to 128
DEFAULT_MEAN_VELOCITY_BINS = np.linspace(0, 128, 33)

# Mean pitch bins, ranging from 0 to 128
DEFAULT_MEAN_PITCH_BINS = np.linspace(0, 128, 33)

# Mean duration bins, logarithmically spaced between 1 and 128 positions (~2.5 bars)
DEFAULT_MEAN_DURATION_BINS = np.logspace(0, 7, 33, base=2)

# --- Output Parameters ---

# Resolution for the output representation
DEFAULT_RESOLUTION = 480

# Maximum length of a single bar in beats (3*4 = 12 beats)
MAX_BAR_LENGTH = 3

# Maximum number of bars in a piece (covers almost all sequences)
MAX_N_BARS = 512

# --- Special Tokens ---

# Define special tokens for padding, unknown, etc.
PAD_TOKEN = '<pad>'
UNK_TOKEN = '<unk>'
BOS_TOKEN = '<bos>'
EOS_TOKEN = '<eos>'
MASK_TOKEN = '<mask>'
SPECIALS = [PAD_TOKEN, UNK_TOKEN, BOS_TOKEN, EOS_TOKEN, MASK_TOKEN]

# --- Keys for Various Musical Features ---

# Define keys for musical features like time signature, bar, etc.
TIME_SIGNATURE_KEY = 'Time Signature'
BAR_KEY = 'Bar'
POSITION_KEY = 'Position'
INSTRUMENT_KEY = 'Instrument'
PITCH_KEY = 'Pitch'
VELOCITY_KEY = 'Velocity'
DURATION_KEY = 'Duration'
TEMPO_KEY = 'Tempo'
CHORD_KEY = 'Chord'
CHORD_QUALITIES = ['maj', 'min', 'dim', 'aug', 'dom7', 'maj7', 'min7', 'None']

NOTE_DENSITY_KEY = 'Note Density'
MEAN_PITCH_KEY = 'Mean Pitch'
MEAN_VELOCITY_KEY = 'Mean Velocity'
MEAN_DURATION_KEY = 'Mean Duration'

# --- Chord Definitions ---

# Define pitch classes and chord maps
PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
CHORD_MAPS = {
    'maj': [0, 4],
    'min': [0, 3],
    'dim': [0, 3, 6],
    'aug': [0, 4, 8],
    'dom7': [0, 4, 10],
    'maj7': [0, 4, 11],
    'min7': [0, 3, 10]
}

# Define chord insiders and outsiders
CHORD_INSIDERS = {
    'maj': [7],
    'min': [7],
    'dim': [9],
    'aug': [],
    'dom7': [7],
    'maj7': [7],
    'min7': [7]
}

CHORD_OUTSIDERS_1 = {
    'maj': [2, 5, 9],
    'min': [2, 5, 8],
    'dim': [2, 5, 10],
    'aug': [2, 5, 9],
    'dom7': [2, 5, 9],
    'maj7': [2, 5, 9],
    'min7': [2, 5, 8]
}

CHORD_OUTSIDERS_2 = {
    'maj': [1, 3, 6, 8, 10, 11],
    'min': [1, 4, 6, 9, 11],
    'dim': [1, 4, 7, 8, 11],
    'aug': [1, 3, 6, 7, 10],
    'dom7': [1, 3, 6, 8, 11],
    'maj7': [1, 3, 6, 8, 10],
    'min7': [1, 4, 6, 9, 11]
}

import pretty_midi

from collections import Counter
from torchtext.vocab import vocab
from torch import Tensor

import constants as const


def get_instrument_tokens(key=const.INSTRUMENT_KEY):
    tokens = [f'{key}_{pretty_midi.program_to_instrument_name(i)}' for i in range(128)]
    tokens.append(f'{key}_drum')
    return tokens


def get_chord_tokens(key=const.CHORD_KEY, qualities=const.CHORD_QUALITIES):
    pitch_classes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    chords = [f'{root}:{quality}' for root in pitch_classes for quality in qualities]
    chords.append('N:N')

    tokens = [f'{key}_{chord}' for chord in chords]
    return tokens


def get_time_signature_tokens(key=const.TIME_SIGNATURE_KEY, max_bar_length=const.MAX_BAR_LENGTH):
    denominators = [2, 4, 8, 16]
    time_sigs = [f'{p}/{q}' for q in denominators for p in range(1, max_bar_length * q + 1)]
    tokens = [f'{key}_{time_sig}' for time_sig in time_sigs]
    return tokens


def get_pitch_tokens(pitch_key=const.PITCH_KEY):
    tokens = [f'{pitch_key}_{i}' for i in range(128)] + [f'{pitch_key}_drum_{i}' for i in range(128)]
    return tokens


def get_velocity_tokens(key=const.VELOCITY_KEY, bins=const.DEFAULT_VELOCITY_BINS):
    tokens = [f'{key}_{i}' for i in range(len(bins))]
    return tokens


def get_duration_tokens(key=const.DURATION_KEY, bins=const.DEFAULT_DURATION_BINS):
    tokens = [f'{key}_{i}' for i in range(len(bins))]
    return tokens


def get_tempo_tokens(key=const.TEMPO_KEY, bins=const.DEFAULT_TEMPO_BINS):
    tokens = [f'{key}_{i}' for i in range(len(bins))]
    return tokens


def get_bar_tokens(key=const.BAR_KEY, max_n_bars=const.MAX_N_BARS):
    tokens = [f'{key}_{i}' for i in range(max_n_bars)]
    return tokens


def get_position_token(key=const.POSITION_KEY, max_bar_length=const.MAX_BAR_LENGTH,
                       default_pos=const.DEFAULT_POS_PER_QUARTER):
    tokens = [f'{key}_{i}' for i in range(max_bar_length * 4 * default_pos)]
    return tokens


def get_density_tokens(key=const.NOTE_DENSITY_KEY, bins=const.DEFAULT_NOTE_DENSITY_BINS):
    tokens = [f'{key}_{i}' for i in range(len(bins))]
    return tokens


def get_mean_velocity_tokens(key=const.MEAN_VELOCITY_KEY, bins=const.DEFAULT_MEAN_VELOCITY_BINS):
    tokens = [f'{key}_{i}' for i in range(len(bins))]
    return tokens


def get_mean_pitch_tokens(key=const.MEAN_PITCH_KEY, bins=const.DEFAULT_MEAN_PITCH_BINS):
    tokens = [f'{key}_{i}' for i in range(len(bins))]
    return tokens


def get_mean_duration_tokens(key=const.MEAN_DURATION_KEY, bins=const.DEFAULT_MEAN_DURATION_BINS):
    tokens = [f'{key}_{i}' for i in range(len(bins))]
    return tokens


def get_midi_tokens():
    instrument_tokens = get_instrument_tokens()
    pitch_tokens = get_pitch_tokens()
    velocity_tokens = get_velocity_tokens()
    duration_tokens = get_duration_tokens()
    tempo_tokens = get_tempo_tokens()
    bar_tokens = get_bar_tokens()
    position_tokens = get_position_token()
    time_sig_tokens = get_time_signature_tokens()

    return (
            time_sig_tokens +
            tempo_tokens +
            instrument_tokens +
            pitch_tokens +
            velocity_tokens +
            duration_tokens +
            bar_tokens +
            position_tokens
    )


class Vocab:
    def __init__(self, counter, specials=const.SPECIALS, unk_token=const.UNK_TOKEN):
        self.vocab = vocab(counter)

        self.specials = specials
        for i, token in enumerate(self.specials):  # Add specials token first
            self.vocab.insert_token(token, i)

        if unk_token in specials:  # If OOV return UNK_TOKEN
            self.vocab.set_default_index(self.vocab.get_stoi()[unk_token])

    def to_i(self, token):  # token 2 idx
        return self.vocab.get_stoi()[token]

    def to_s(self, idx):  # idx 2 token
        if idx >= len(self.vocab):
            return const.UNK_TOKEN
        else:
            return self.vocab.get_itos()[idx]

    def __len__(self):
        return len(self.vocab)

    def encode(self, seq):
        return self.vocab(seq)

    def decode(self, seq):
        if isinstance(seq, Tensor):
            seq = seq.numpy()
        return self.vocab.lookup_tokens(seq)

    def check(self):
        return {self.to_s(i): i for i in range(len(self.vocab))}


class RemiVocab(Vocab):
    def __init__(self):
        midi_tokens = get_midi_tokens()
        chord_tokens = get_chord_tokens()

        self.tokens = midi_tokens + chord_tokens

        counter = Counter(self.tokens)
        super().__init__(counter)


class DescriptionVocab(Vocab):
    def __init__(self):
        time_sig_tokens = get_time_signature_tokens()
        instrument_tokens = get_instrument_tokens()
        chord_tokens = get_chord_tokens()

        bar_tokens = get_bar_tokens()
        density_tokens = get_density_tokens()
        velocity_tokens = get_mean_velocity_tokens()
        pitch_tokens = get_mean_pitch_tokens()
        duration_tokens = get_mean_duration_tokens()

        self.tokens = (
                time_sig_tokens +
                instrument_tokens +
                chord_tokens +
                density_tokens +
                velocity_tokens +
                pitch_tokens +
                duration_tokens +
                bar_tokens
        )

        counter = Counter(self.tokens)
        super().__init__(counter)


def test():
    from midi2remi import RemiPlus

    test_midi = '/Users/baron/Desktop/SymbolicMusicProject/data_processing/test.mid'
    data = RemiPlus(test_midi, do_extract_chords=True, strict=True)

    remi_vocab = RemiVocab()
    print(f'RemiVocab: {remi_vocab.check()}')
    print('#####################')
    remi_event = data.get_remi_events()
    print(f'Original: {remi_event[:20]}')
    encoded = remi_vocab.encode(remi_event[:20])
    print(f'Encoded: {encoded}')
    print(f'Decoded: {remi_vocab.decode(encoded)}')
    print('#####################')

    des_vocab = DescriptionVocab()
    print(f'DesVocab: {des_vocab.check()}')
    print('#####################')
    des_event = data.get_description()
    print(f'Original: {des_event[:20]}')
    encoded = des_vocab.encode(des_event[:20])
    print(f'Encoded: {encoded}')
    print(f'Decoded: {des_vocab.decode(encoded)}')


if __name__ == '__main__':
    test()

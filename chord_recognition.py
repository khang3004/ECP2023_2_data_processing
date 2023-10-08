import numpy as np
import utils
from music_obj import Item
import constants as const


def sequencing(chroma):
    """Generate chord candidates based on chroma features.

    Args:
        chroma (np.array): Chroma features.

    Returns:
        dict: Chord candidates with root notes as keys.
    """

    candidates = {}
    for index in range(len(chroma)):
        if chroma[index]:
            root_note = index
            _chroma = np.roll(chroma, -root_note)
            sequence = np.where(_chroma == 1)[0]
            candidates[root_note] = list(sequence)
    return candidates


def scoring(candidates):
    """Score chord candidates based on their quality.

    Args:
        candidates (dict): Chord candidates.

    Returns:
        tuple: Scores and qualities of candidates.
    """

    scores = {}
    qualities = {}
    for root_note, sequence in candidates.items():
        if 3 not in sequence and 4 not in sequence:
            scores[root_note] = -100
            qualities[root_note] = 'None'
        elif 3 in sequence and 4 in sequence:
            scores[root_note] = -100
            qualities[root_note] = 'None'
        else:
            # decide quality
            if 3 in sequence:
                if 6 in sequence:
                    quality = 'dim'
                else:
                    if 10 in sequence:
                        quality = 'min7'
                    else:
                        quality = 'min'
            elif 4 in sequence:
                if 8 in sequence:
                    quality = 'aug'
                else:
                    if 10 in sequence:
                        quality = 'dom7'
                    elif 11 in sequence:
                        quality = 'maj7'
                    else:
                        quality = 'maj'
            # decide score
            maps = const.CHORD_MAPS.get(quality)
            _notes = [n for n in sequence if n not in maps]
            score = 0
            for n in _notes:
                if n in const.CHORD_OUTSIDERS_1.get(quality):
                    score -= 1
                elif n in const.CHORD_OUTSIDERS_2.get(quality):
                    score -= 2
                elif n in const.CHORD_INSIDERS.get(quality):
                    score += 10
            scores[root_note] = score
            qualities[root_note] = quality
    return scores, qualities


def find_chord(chroma, threshold=10):
    """Find the best chord based on chroma features.

    Args:
        chroma (np.array): Chroma features.
        threshold (int): Threshold for chroma features.

    Returns:
        tuple: Root note, quality, bass note, and score.
    """
    chroma = np.sum(chroma, axis=1)
    chroma = np.array([1 if c > threshold else 0 for c in chroma])
    if np.sum(chroma) == 0:
        return 'N', 'N', 'N', 10
    else:
        candidates = sequencing(chroma=chroma)
        scores, qualities = scoring(candidates=candidates)
        # bass note
        sorted_notes = []
        for i, v in enumerate(chroma):
            if v > 0:
                sorted_notes.append(int(i % 12))
        bass_note = sorted_notes[0]
        # root note
        __root_note = []
        _max = max(scores.values())
        for _root_note, score in scores.items():
            if score == _max:
                __root_note.append(_root_note)
        if len(__root_note) == 1:
            root_note = __root_note[0]
        else:
            # TODO: what should i do
            for n in sorted_notes:
                if n in __root_note:
                    root_note = n
                    break
        # quality
        quality = qualities.get(root_note)
        # score
        score = scores.get(root_note)
        return const.PITCH_CLASSES[root_note], quality, const.PITCH_CLASSES[bass_note], score


def get_candidates(chroma, max_tick, intervals=None):
    """Generate chord candidates for different intervals of a chroma representation."""
    if intervals is None:
        intervals = [1, 2, 3, 4]
    candidates = {}

    for interval in intervals:
        for start_beat in range(max_tick):
            # Determine the chroma based on the interval
            end_beat = min(start_beat + interval, max_tick)
            _chroma = chroma[:, start_beat:end_beat]

            # Find the chord for the chroma
            root_note, quality, bass_note, score = find_chord(chroma=_chroma)

            # Store the chord information in the candidates dictionary
            candidates.setdefault(start_beat, {})[end_beat] = (root_note, quality, bass_note, score)

    return candidates


def dedupe(chords):
    """Remove duplicate chords.

    Args:
        chords (list): List of chords.

    Returns:
        list: List of unique chords.
    """
    if len(chords) == 0:
        return []
    deduped = []
    start, end, chord = chords[0]
    for (curr, next_chord) in zip(chords[:-1], chords[1:]):
        if chord == next_chord[2]:
            end = next_chord[1]
        else:
            deduped.append([start, end, chord])
            start, end, chord = next_chord
    deduped.append([start, end, chord])
    return deduped


def dynamic(candidates, max_tick):
    """Dynamic programming approach to find the best chord sequence.

    Args:
        candidates (dict): Chord candidates.
        max_tick (int): Maximum tick value.

    Returns:
        list: Best chord sequence.
    """

    # store index of best chord at each position
    chords = [None for _ in range(max_tick + 1)]
    # store score of best chords at each position
    scores = np.zeros(max_tick + 1)
    scores[1:].fill(np.NINF)

    start_tick = 0
    while start_tick < max_tick:
        if start_tick in candidates:
            for i, (end_tick, candidate) in enumerate(candidates.get(start_tick).items()):
                root_note, quality, bass_note, score = candidate
                # if this candidate is best yet, update scores and chords
                if scores[end_tick] < scores[start_tick] + score:
                    scores[end_tick] = scores[start_tick] + score
                    if root_note == bass_note:
                        chord = '{}:{}'.format(root_note, quality)
                    else:
                        chord = '{}:{}/{}'.format(root_note, quality, bass_note)
                    chords[end_tick] = (start_tick, end_tick, chord)
        start_tick += 1
    # Read the best path
    start_tick = len(chords) - 1
    results = []
    while start_tick > 0:
        chord = chords[start_tick]
        start_tick = chord[0]
        results.append(chord)

    return list(reversed(results))


def extract(midi):
    # Extract beat and chroma information from the MIDI file
    beats = utils.get_beats(midi)
    chroma = utils.get_chroma(midi, beats)

    # Retrieve potential chord candidates based on chroma data
    candidates = get_candidates(chroma, max_tick=len(beats))

    # Use a dynamic programming approach to select the best set of chords
    selected_chords = dynamic(candidates=candidates, max_tick=len(beats))

    # Remove duplicate chords
    unique_chords = dedupe(selected_chords)

    # Map chord start and end times from beat indices to actual time values
    mapped_chords = []
    for chord in unique_chords:
        start_time = beats[chord[0]]
        end_time = midi.get_end_time() if chord[1] >= len(beats) else beats[chord[1]]
        mapped_chords.append([start_time, end_time, chord[2]])

    return mapped_chords


def extract_chords(midi):

    end_tick = utils.get_end_tick(midi)
    # If sequence is shorter than 1/4th note,
    # consider it empty and return an empty list
    if end_tick < midi.resolution:
        return []

    raw_chords = extract(midi)
    output = []
    # Convert raw chords to Item objects
    for chord in raw_chords:
        output.append(Item(
            name='Chord',
            start=midi.time_to_tick(chord[0]),
            end=midi.time_to_tick(chord[1]),
            velocity=None,
            pitch=chord[2].split('/')[0]
        ))
    # If there are no chords or the first chord doesn't start at 0,
    # add a 'N:N' chord at the beginning
    if not output or output[0].start > 0:
        end = output[0].start if output else end_tick
        output.insert(0, Item(
            name='Chord',
            start=0,
            end=end,
            velocity=None,
            pitch='N:N'
        ))
    return output


def test():
    file = '/Users/baron/Desktop/SymbolicMusicProject/data_processing/test.mid'
    test_midi = utils.load_midi(file, strict=False)
    # beats = utils.get_beats(test_midi)
    # print(f'Beat: {beats}')
    # print('#########################')
    # chroma = utils.get_chroma(test_midi, beats)
    # print(f'Chroma: {chroma}')
    # print('#########################')
    # candidates = get_candidates(chroma, max_tick=len(beats))
    # print(f'Candidates: {candidates}')
    # print('#########################')
    # chords = dynamic(candidates=candidates, max_tick=len(beats))
    # print(f'Dynamic Chords: {chords}')
    # print('#########################')
    # chords = dedupe(chords)
    # print(f'Deduped Chords: {chords}')
    print('#########################')
    print(f'Extracted Chords: {extract(test_midi)}')
    print('#########################')
    # print(f'Extracted Chords Items: {extract_chords(test_midi)}')


if __name__ == '__main__':
    test()

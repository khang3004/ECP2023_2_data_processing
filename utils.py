import pretty_midi
import numpy as np
from music_obj import Item
import constants as const


def load_midi(file, strict=False):
    """Load a MIDI file using PrettyMIDI.

    Args:
        file (str or pretty_midi.PrettyMIDI): Path to the MIDI file or a PrettyMIDI object.
        strict (bool, optional): If True, raises an error if no time signature is defined. Defaults to False.

    Returns:
        pretty_midi.PrettyMIDI: Loaded MIDI object.

    Raises:
        ValueError: If strict is True and no time signature is defined in the MIDI file.
    """
    # Check if the input is already a PrettyMIDI object
    if isinstance(file, pretty_midi.PrettyMIDI):
        midi = file
    else:
        # Load the MIDI file using PrettyMIDI
        midi = pretty_midi.PrettyMIDI(file)

    # If strict mode is enabled, check for time signature
    if strict and len(midi.time_signature_changes) == 0:
        raise ValueError("Invalid MIDI file: No time signature defined")

    return midi


def get_beats(midi):
    """Get beat timings from the MIDI file.

    Args:
        midi (pretty_midi.PrettyMIDI): Loaded MIDI object.

    Returns:
        numpy.ndarray: Array of beat timings.
    """
    return midi.get_beats()


def get_chroma(midi, beats):
    """Get chroma features from the MIDI file.

    Args:
        midi (pretty_midi.PrettyMIDI): Loaded MIDI object.
        beats (numpy.ndarray): Array of beat timings.

    Returns:
        numpy.ndarray: Chroma features.
    """
    return midi.get_chroma(times=beats)


def get_end_tick(midi):
    """Get the end tick of the MIDI file.

    Args:
        midi (pretty_midi.PrettyMIDI): Loaded MIDI object.

    Returns:
        int: End tick of the MIDI file.
    """
    return midi.time_to_tick(midi.get_end_time())


def quantize_items(midi, note_items):
    """Quantize note timings to align with a grid.

    Args:
        midi (pretty_midi.PrettyMIDI): Loaded MIDI object.
        note_items (list of Item): List of note items.

    Returns:
        list of Item: List of quantized note items.
    """
    ticks = midi.resolution / const.DEFAULT_POS_PER_QUARTER
    end_tick = get_end_tick(midi)
    grids = np.arange(0, max(midi.resolution, end_tick), ticks)
    for item in note_items:
        index = np.searchsorted(grids, item.start, side='right')
        if index > 0:
            index -= 1
        shift = round(grids[index]) - item.start
        item.start += shift
        item.end += shift
    return note_items


def read_note_items(midi):
    """Read note and pedal events from the MIDI file.

    Args:
        midi (pretty_midi.PrettyMIDI): Loaded MIDI object.

    Returns:
        list of Item: List of note and pedal items.
    """
    note_items = []
    for instrument in midi.instruments:
        pedal_events = [event for event in instrument.control_changes if event.number == 64]
        pedal_pressed = False
        start = None
        pedals = []
        for e in pedal_events:
            if e.value >= 64 and not pedal_pressed:
                pedal_pressed = True
                start = e.time
            elif e.value < 64 and pedal_pressed:
                pedal_pressed = False
                pedals.append(Item(name='Pedal', start=start, end=e.time))
                start = e.time

        notes = instrument.notes
        notes.sort(key=lambda x: (x.start, x.pitch))

        if instrument.is_drum:
            instrument_name = 'drum'
        else:
            instrument_name = instrument.program

        pedal_idx = 0
        for note in notes:
            pedal_candidates = [(i + pedal_idx, pedal) for i, pedal in enumerate(pedals[pedal_idx:]) if
                                note.end >= pedal.start and note.start < pedal.end]
            if len(pedal_candidates) > 0:
                pedal_idx = pedal_candidates[0][0]
                pedal = pedal_candidates[-1][1]
            else:
                pedal = Item(name='Pedal', start=0, end=0)

            note_items.append(Item(
                name='Note',
                start=midi.time_to_tick(note.start),
                end=midi.time_to_tick(max(note.end, pedal.end)),
                velocity=note.velocity,
                pitch=note.pitch,
                instrument=instrument_name))
    note_items.sort(key=lambda x: (x.start, x.pitch))

    # Quantize
    note_items = quantize_items(midi, note_items)
    return note_items


def read_tempo_items(midi):
    """Read tempo events from the MIDI file.

    Args:
        midi (pretty_midi.PrettyMIDI): Loaded MIDI object.

    Returns:
        list of Item: List of tempo items.
    """
    tempo_items = []
    times, tempo = midi.get_tempo_changes()
    for time, tempo in zip(times, tempo):
        tempo_items.append(Item(
            name='Tempo',
            start=midi.time_to_tick(time),
            end=None,
            velocity=None,
            pitch=int(tempo)))
    tempo_items.sort(key=lambda x: x.start)

    # expand to all beat
    max_tick = midi.time_to_tick(midi.get_end_time())
    existing_ticks = {item.start: item.pitch for item in tempo_items}
    wanted_ticks = np.arange(0, max_tick + 1, const.DEFAULT_RESOLUTION)
    output = []
    for tick in wanted_ticks:
        if tick in existing_ticks:
            output.append(Item(
                name='Tempo',
                start=tick,
                end=None,
                velocity=None,
                pitch=existing_ticks[tick]))
        else:
            output.append(Item(
                name='Tempo',
                start=midi.time_to_tick(tick),
                end=None,
                velocity=None,
                pitch=output[-1].pitch))
    return output


def get_key(item):
    """Sort and group items by their start time, type, and other attributes.

    Args:
        item (Item): Item object.

    Returns:
        tuple: Sorting key.
    """
    type_priority = {
        'Chord': 0,
        'Tempo': 1,
        'Note': 2
    }
    return (
        item.start,  # order by time
        type_priority[item.name],  # chord events first, then tempo events, then note events
        -1 if item.instrument == 'drum' else item.instrument,  # order by instrument
        item.pitch  # order by note pitch
    )


def group_items(midi, note_items, chord_items, tempo_items):
    """Group items by bars.

    Args:
        midi (pretty_midi.PrettyMIDI): Loaded MIDI object.
        note_items (list of Item): List of note items.
        chord_items (list of Item): List of chord items.
        tempo_items (list of Item): List of tempo items.

    Returns:
        list: List of grouped items.
    """
    if chord_items:
        items = chord_items + tempo_items + note_items
    else:
        items = tempo_items + note_items

    items.sort(key=get_key)
    downbeats = midi.get_downbeats()
    downbeats = np.concatenate([downbeats, [midi.get_end_time()]])

    groups = []
    for db1, db2 in zip(downbeats[:-1], downbeats[1:]):
        db1, db2 = midi.time_to_tick(db1), midi.time_to_tick(db2)
        insiders = []
        for item in items:
            if (item.start >= db1) and (item.start < db2):
                insiders.append(item)
        overall = [db1] + insiders + [db2]
        groups.append(overall)

    # Trim empty groups from the beginning and end
    for idx in [0, -1]:
        while len(groups) > 0:
            group = groups[idx]
            notes = [item for item in group[1:-1] if item.name == 'Note']
            if len(notes) == 0:
                groups.pop(idx)
            else:
                break

    return groups


def tick_to_position(tick, resolution):
    """Convert tick to position based on resolution.

    Args:
        tick (int): Tick value.
        resolution (int): Resolution value.

    Returns:
        int: Position value.
    """
    return round(tick / resolution * const.DEFAULT_POS_PER_QUARTER)


def get_time_signature(midi, start):
    """Get the time signature at a specific tick.

    Args:
        midi (pretty_midi.PrettyMIDI): Loaded MIDI object.
        start (int): Tick value.

    Returns:
        pretty_midi.TimeSignature: Time signature object.
    """
    # This method assumes that time signature changes don't happen within a bar
    # which is a convention that commonly holds
    time_sig = None
    for curr_sig, next_sig in zip(midi.time_signature_changes[:-1], midi.time_signature_changes[1:]):
        if midi.time_to_tick(curr_sig.time) <= start < midi.time_to_tick(next_sig.time):
            time_sig = curr_sig
            break
    if time_sig is None:
        time_sig = midi.time_signature_changes[-1]
    return time_sig


def get_ticks_per_bar(midi, start):
    """Get the number of ticks per bar at a specific tick.

    Args:
        midi (pretty_midi.PrettyMIDI): Loaded MIDI object.
        start (int): Tick value.

    Returns:
        int: Number of ticks per bar.
    """
    time_sig = get_time_signature(midi, start)
    quarters_per_bar = 4 * time_sig.numerator / time_sig.denominator
    return midi.resolution * quarters_per_bar


def get_positions_per_bar(midi, start=None, time_sig=None):
    """Get the number of positions per bar at a specific tick.

    Args:
        midi (pretty_midi.PrettyMIDI): Loaded MIDI object.
        start (int, optional): Tick value. Defaults to None.
        time_sig (pretty_midi.TimeSignature, optional): Time signature object. Defaults to None.

    Returns:
        int: Number of positions per bar.
    """
    if time_sig is None:
        time_sig = get_time_signature(midi, start)
    quarters_per_bar = 4 * time_sig.numerator / time_sig.denominator
    positions_per_bar = int(const.DEFAULT_POS_PER_QUARTER * quarters_per_bar)
    return positions_per_bar


def get_time(reference, bar, pos):
    """Calculate the time in seconds for a given bar and position.

    Args:
        reference (dict): Reference dictionary containing time, tempo, and time signature.
        bar (int): Bar number.
        pos (int): Position within the bar.

    Returns:
        float: Time in seconds.
    """
    time_sig = reference['time_sig']
    num, denom = time_sig.numerator, time_sig.denominator
    # Quarters per bar, assuming 4 quarters per whole note
    qpb = 4 * num / denom
    ref_pos = reference['pos']
    d_bars = bar - ref_pos[0]
    d_pos = (pos - ref_pos[1]) + d_bars * qpb * const.DEFAULT_POS_PER_QUARTER
    d_quarters = d_pos / const.DEFAULT_POS_PER_QUARTER
    # Convert quarters to seconds
    dt = d_quarters / reference['tempo'] * 60
    return reference['time'] + dt


def test():
    file = '../MusicData/Lakh_MIDI_Dataset/LMD_full/lmd_full/2/2a0a712b4b00f3df2d4fa50fe21f43cb.mid'
    test_midi = load_midi(file, strict=True)
    beats = read_note_items(test_midi)
    # print(beats)


if __name__ == '__main__':
    test()
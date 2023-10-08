import constants as const
import pretty_midi
import utils


#############################################################################################
# WRITE MIDI
#############################################################################################

def remi2midi(events, bpm=120, time_signature=(4, 4), polyphony_limit=16):
    tempo_changes = [event for event in events if f"{const.TEMPO_KEY}_" in event]
    if len(tempo_changes) > 0:
        bpm = const.DEFAULT_TEMPO_BINS[int(tempo_changes[0].split('_')[-1])]

    midi = pretty_midi.PrettyMIDI(initial_tempo=bpm)
    num, denom = time_signature
    midi.time_signature_changes.append(pretty_midi.TimeSignature(num, denom, 0))
    current_time_sig = midi.time_signature_changes[0]

    instruments = {}

    # Use implicit timeline: keep track of last tempo/time signature change event
    # and calculate time difference relative to that
    last_tl_event = {
        'time': 0,
        'pos': (0, 0),
        'time_sig': current_time_sig,
        'tempo': bpm
    }

    bar = -1
    n_notes = 0
    polyphony_control = {}
    for i, event in enumerate(events):
        if event == const.EOS_TOKEN:
            break

        if bar not in polyphony_control:
            polyphony_control[bar] = {}

        if f"{const.BAR_KEY}_" in events[i]:
            # Next bar is starting
            bar += 1
            polyphony_control[bar] = {}

            if i + 1 < len(events) and f"{const.TIME_SIGNATURE_KEY}_" in events[i + 1]:
                num, denom = events[i + 1].split('_')[-1].split('/')
                num, denom = int(num), int(denom)
                current_time_sig = last_tl_event['time_sig']
                if num != current_time_sig.numerator or denom != current_time_sig.denominator:
                    time = utils.get_time(last_tl_event, bar, 0)
                    time_sig = pretty_midi.TimeSignature(num, denom, time)
                    midi.time_signature_changes.append(time_sig)
                    last_tl_event['time'] = time
                    last_tl_event['pos'] = (bar, 0)
                    last_tl_event['time_sig'] = time_sig

        elif i + 1 < len(events) and \
                f"{const.POSITION_KEY}_" in events[i] and \
                f"{const.TEMPO_KEY}_" in events[i + 1]:
            position = int(events[i].split('_')[-1])
            tempo_idx = int(events[i + 1].split('_')[-1])
            tempo = const.DEFAULT_TEMPO_BINS[tempo_idx]

            if tempo != last_tl_event['tempo']:
                time = utils.get_time(last_tl_event, bar, position)
                last_tl_event['time'] = time
                last_tl_event['pos'] = (bar, position)
                last_tl_event['tempo'] = tempo

        elif i + 4 < len(events) and \
                f"{const.POSITION_KEY}_" in events[i] and \
                f"{const.INSTRUMENT_KEY}_" in events[i + 1] and \
                f"{const.PITCH_KEY}_" in events[i + 2] and \
                f"{const.VELOCITY_KEY}_" in events[i + 3] and \
                f"{const.DURATION_KEY}_" in events[i + 4]:
            # get position
            position = int(events[i].split('_')[-1])
            if position not in polyphony_control[bar]:
                polyphony_control[bar][position] = {}

            # get instrument
            instrument_name = events[i + 1].split('_')[-1]
            if instrument_name not in polyphony_control[bar][position]:
                polyphony_control[bar][position][instrument_name] = 0
            elif polyphony_control[bar][position][instrument_name] >= polyphony_limit:
                # If number of notes exceeds polyphony limit, omit this note
                continue

            if instrument_name not in instruments:
                if instrument_name == 'drum':
                    instrument = pretty_midi.Instrument(0, is_drum=True)
                else:
                    program = pretty_midi.instrument_name_to_program(instrument_name)
                    instrument = pretty_midi.Instrument(program)
                instruments[instrument_name] = instrument
            else:
                instrument = instruments[instrument_name]

            # get pitch
            pitch = int(events[i + 2].split('_')[-1])
            # get velocity
            velocity_index = int(events[i + 3].split('_')[-1])
            velocity = min(127, const.DEFAULT_VELOCITY_BINS[velocity_index])
            # get duration
            duration_index = int(events[i + 4].split('_')[-1])
            duration = const.DEFAULT_DURATION_BINS[duration_index]
            # create not and add to instrument
            start = utils.get_time(last_tl_event, bar, position)
            end = utils.get_time(last_tl_event, bar, position + duration)
            note = pretty_midi.Note(velocity=velocity,
                                    pitch=pitch,
                                    start=start,
                                    end=end)
            instrument.notes.append(note)
            n_notes += 1
            polyphony_control[bar][position][instrument_name] += 1

    for instrument in instruments.values():
        midi.instruments.append(instrument)
    return midi


def test():
    from midi2remi import RemiPlus
    import os

    test_midi = '/Users/baron/Desktop/SymbolicMusicProject/data_processing/test.mid'
    data = RemiPlus(test_midi, do_extract_chords=True, strict=True)

    remi_event = data.get_remi_events()
    midi = remi2midi(remi_event)

    out_dir = '/Users/baron/Desktop/SymbolicMusicProject/data_processing/'
    file_name = 'reverted.mid'
    print(f"Saving to {out_dir}/{file_name}")
    midi.write(os.path.join(out_dir, file_name))


if __name__ == '__main__':
    test()

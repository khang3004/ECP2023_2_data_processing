import numpy as np
import pretty_midi

import utils
from music_obj import Event
import constants as const
import chord_recognition


class RemiPlus:
    def __init__(self, file, do_extract_chords=True, strict=False):
        self.midi = utils.load_midi(file, strict)

        self.resolution = self.midi.resolution

        # read notes and tempo changes from midi (assume there is only one track)
        self.note_items = utils.read_note_items(self.midi)
        self.tempo_items = utils.read_tempo_items(self.midi)
        if do_extract_chords:
            self.chord_items = chord_recognition.extract_chords(self.midi)
        self.groups = utils.group_items(self.midi, self.note_items, self.chord_items, self.tempo_items)

        if strict and len(self.note_items) == 0:
            raise ValueError("Invalid MIDI file: No notes found, empty file.")

    # item to event
    def get_remi_events(self):
        events = []
        n_downbeat = 0
        current_chord = None
        current_tempo = None
        for i in range(len(self.groups)):
            bar_st, bar_et = self.groups[i][0], self.groups[i][-1]
            n_downbeat += 1
            positions_per_bar = utils.get_positions_per_bar(self.midi, bar_st)
            if positions_per_bar <= 0:
                raise ValueError('Invalid REMI file: There must be at least 1 position per bar.')

            events.append(Event(
                name=const.BAR_KEY,
                time=None,
                value=f'{n_downbeat}',
                text=f'{n_downbeat}'))

            time_sig = utils.get_time_signature(self.midi, bar_st)
            events.append(Event(
                name=const.TIME_SIGNATURE_KEY,
                time=None,
                value=f'{time_sig.numerator}/{time_sig.denominator}',
                text=f'{time_sig.numerator}/{time_sig.denominator}'
            ))

            if current_chord is not None:
                events.append(Event(
                    name=const.POSITION_KEY,
                    time=0,
                    value=f'{0}',
                    text=f'{1}/{positions_per_bar}'))
                events.append(Event(
                    name=const.CHORD_KEY,
                    time=current_chord.start,
                    value=current_chord.pitch,
                    text=f'{current_chord.pitch}'))

            if current_tempo is not None:
                events.append(Event(
                    name=const.POSITION_KEY,
                    time=0,
                    value=f'{0}',
                    text=f'{1}/{positions_per_bar}'))
                tempo = current_tempo.pitch
                index = np.argmin(abs(const.DEFAULT_TEMPO_BINS - tempo))
                events.append(Event(
                    name=const.TEMPO_KEY,
                    time=current_tempo.start,
                    value=index,
                    text=f'{tempo}/{const.DEFAULT_TEMPO_BINS[index]}'))

            quarters_per_bar = 4 * time_sig.numerator / time_sig.denominator
            ticks_per_bar = self.midi.resolution * quarters_per_bar
            flags = np.linspace(bar_st, bar_st + ticks_per_bar, positions_per_bar, endpoint=False)
            for item in self.groups[i][1:-1]:
                # position
                index = np.argmin(abs(flags - item.start))
                pos_event = Event(
                    name=const.POSITION_KEY,
                    time=item.start,
                    value=f'{index}',
                    text=f'{index + 1}/{positions_per_bar}')

                if item.name == 'Note':
                    events.append(pos_event)
                    # instrument
                    if item.instrument == 'drum':
                        name = 'drum'
                    else:
                        name = pretty_midi.program_to_instrument_name(item.instrument)
                    events.append(Event(
                        name=const.INSTRUMENT_KEY,
                        time=item.start,
                        value=name,
                        text='{}'.format(name)))
                    # pitch
                    events.append(Event(
                        name=const.PITCH_KEY,
                        time=item.start,
                        value='drum_{}'.format(item.pitch) if name == 'drum' else item.pitch,
                        text='{}'.format(pretty_midi.note_number_to_name(item.pitch))))
                    # velocity
                    velocity_index = np.argmin(abs(const.DEFAULT_VELOCITY_BINS - item.velocity))
                    events.append(Event(
                        name=const.VELOCITY_KEY,
                        time=item.start,
                        value=velocity_index,
                        text='{}/{}'.format(item.velocity, const.DEFAULT_VELOCITY_BINS[velocity_index])))
                    # duration
                    duration = utils.tick_to_position(item.end - item.start, self.midi.resolution)
                    index = np.argmin(abs(const.DEFAULT_DURATION_BINS - duration))
                    events.append(Event(
                        name=const.DURATION_KEY,
                        time=item.start,
                        value=index,
                        text=f'{duration}/{const.DEFAULT_DURATION_BINS[index]}'))
                elif item.name == 'Chord':
                    if current_chord is None or item.pitch != current_chord.pitch:
                        events.append(pos_event)
                        events.append(Event(
                            name=const.CHORD_KEY,
                            time=item.start,
                            value=item.pitch,
                            text=f'{item.pitch}'))
                        current_chord = item
                elif item.name == 'Tempo':
                    if current_tempo is None or item.pitch != current_tempo.pitch:
                        events.append(pos_event)
                        tempo = item.pitch
                        index = np.argmin(abs(const.DEFAULT_TEMPO_BINS - tempo))
                        events.append(Event(
                            name=const.TEMPO_KEY,
                            time=item.start,
                            value=index,
                            text=f'{tempo}/{const.DEFAULT_TEMPO_BINS[index]}'))
                        current_tempo = item

        return [f'{e.name}_{e.value}' for e in events]

    def get_description(self,
                        omit_time_sig=False,
                        omit_instruments=False,
                        omit_chords=False,
                        omit_meta=False):
        events = []
        n_downbeat = 0
        current_chord = None

        for i in range(len(self.groups)):
            bar_st, bar_et = self.groups[i][0], self.groups[i][-1]
            n_downbeat += 1
            time_sig = utils.get_time_signature(self.midi, bar_st)
            positions_per_bar = utils.get_positions_per_bar(midi=self.midi, time_sig=time_sig)
            if positions_per_bar <= 0:
                raise ValueError('Invalid REMI file: There must be at least 1 position in each bar.')

            events.append(Event(
                name=const.BAR_KEY,
                time=None,
                value=f'{n_downbeat}',
                text=f'{n_downbeat}'))

            if not omit_time_sig:
                events.append(Event(
                    name=const.TIME_SIGNATURE_KEY,
                    time=None,
                    value=f'{time_sig.numerator}/{time_sig.denominator}',
                    text=f'{time_sig.numerator}/{time_sig.denominator}',
                ))

            if not omit_meta:
                notes = [item for item in self.groups[i][1:-1] if item.name == 'Note']
                n_notes = len(notes)
                velocities = np.array([item.velocity for item in notes])
                pitches = np.array([item.pitch for item in notes])
                durations = np.array([item.end - item.start for item in notes])

                note_density = n_notes / positions_per_bar
                index = np.argmin(abs(const.DEFAULT_NOTE_DENSITY_BINS - note_density))
                events.append(Event(
                    name=const.NOTE_DENSITY_KEY,
                    time=None,
                    value=index,
                    text=f'{note_density:.2f}/{const.DEFAULT_NOTE_DENSITY_BINS[index]:.2f}'
                ))

                # will be 0 if there's no notes
                mean_velocity = velocities.mean() if len(velocities) > 0 else np.nan
                index = np.argmin(abs(const.DEFAULT_MEAN_VELOCITY_BINS - mean_velocity))
                events.append(Event(
                    name=const.MEAN_VELOCITY_KEY,
                    time=None,
                    value=index if mean_velocity != np.nan else 'NaN',
                    text=f'{mean_velocity:.2f}/{const.DEFAULT_MEAN_VELOCITY_BINS[index]:.2f}'
                ))

                # will be 0 if there's no notes
                mean_pitch = pitches.mean() if len(pitches) > 0 else np.nan
                index = np.argmin(abs(const.DEFAULT_MEAN_PITCH_BINS - mean_pitch))
                events.append(Event(
                    name=const.MEAN_PITCH_KEY,
                    time=None,
                    value=index if mean_pitch != np.nan else 'NaN',
                    text=f'{mean_pitch:.2f}/{const.DEFAULT_MEAN_PITCH_BINS[index]:.2f}'
                ))

                # will be 1 if there's no notes
                mean_duration = durations.mean() if len(durations) > 0 else np.nan
                index = np.argmin(abs(const.DEFAULT_MEAN_DURATION_BINS - mean_duration))
                events.append(Event(
                    name=const.MEAN_DURATION_KEY,
                    time=None,
                    value=index if mean_duration != np.nan else 'NaN',
                    text='{mean_duration:.2f}/{DEFAULT_MEAN_DURATION_BINS[index]:.2f}'
                ))

            if not omit_instruments:
                instruments = set([item.instrument for item in notes])
                for instrument in instruments:
                    instrument = pretty_midi.program_to_instrument_name(instrument) if instrument != 'drum' else 'drum'
                    events.append(Event(
                        name=const.INSTRUMENT_KEY,
                        time=None,
                        value=instrument,
                        text=instrument
                    ))

            if not omit_chords:
                chords = [item for item in self.groups[i][1:-1] if item.name == 'Chord']
                if len(chords) == 0 and current_chord is not None:
                    chords = [current_chord]
                elif len(chords) > 0:
                    if chords[0].start > bar_st and current_chord is not None:
                        chords.insert(0, current_chord)
                    current_chord = chords[-1]

                for chord in chords:
                    events.append(Event(
                        name=const.CHORD_KEY,
                        time=None,
                        value=chord.pitch,
                        text='{}'.format(chord.pitch)
                    ))

        return [f'{e.name}_{e.value}' for e in events]


def test():
    test_midi = '/Users/baron/Desktop/SymbolicMusicProject/data_processing/test.mid'
    data = RemiPlus(test_midi, do_extract_chords=True, strict=True)
    print('#####################')
    print(data.get_remi_events()[:20])
    print('#####################')
    print(data.get_description()[:20])


if __name__ == '__main__':
    test()

class Item:
    """Represents a musical item like a note or a chord.

    Attributes:
        name (str): The name of the item (e.g., "Note", "Chord").
        start (float): The start time of the item.
        end (float): The end time of the item.
        velocity (int, optional): The MIDI velocity of the item.
        pitch (int, optional): The MIDI pitch of the item.
        instrument (int, optional): The MIDI instrument number.
    """

    def __init__(self, name, start, end, velocity=None, pitch=None, instrument=None):
        self.name = name
        self.start = start
        self.end = end
        self.velocity = velocity
        self.pitch = pitch
        self.instrument = instrument

    def __repr__(self):
        """Returns a string representation of the Item object for debugging and logging."""
        return f'Item(name={self.name}, start={self.start}, end={self.end}, velocity={self.velocity}, pitch={self.pitch}, instrument={self.instrument})'


class Event:
    """Represents an event that occurs at a specific time, like a tempo change.

    Attributes:
        name (str): The name of the event (e.g., "Tempo Change", "Time Signature").
        time (float): The time at which the event occurs.
        value (float): The value associated with the event (e.g., BPM for a tempo change).
        text (str): Additional text description or metadata for the event.
    """

    def __init__(self, name, time, value, text):
        self.name = name
        self.time = time
        self.value = value
        self.text = text

    def __repr__(self):
        """Returns a string representation of the Event object for debugging and logging."""
        return f'Event(name={self.name}, time={self.time}, value={self.value}, text={self.text})'

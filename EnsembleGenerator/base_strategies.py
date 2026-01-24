from abc import ABC, abstractmethod

class ChordStrategy(ABC):
    @abstractmethod
    def get_notes(self, root_note_number, key_info=None):
        """
        Returns a list of note numbers for the chord.
        key_info: tuple (key_root_index, scale_type) e.g. (0, 'Major')
        """
        pass

class StyleStrategy(ABC):
    @abstractmethod
    def apply(self, chord_notes, bass_note, velocity_scale=1.0, midi_data=None):
        """Returns a list of pretty_midi.Note objects."""
        pass

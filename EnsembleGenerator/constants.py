
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]          # Natural Minor
HARMONIC_MINOR_SCALE = [0, 2, 3, 5, 7, 8, 11] # Harmonic Minor (Raised 7th)
MELODIC_MINOR_SCALE = [0, 2, 3, 5, 7, 9, 11]  # Melodic Minor (Ascending)
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def get_note_name(note_number):
    return NOTE_NAMES[note_number % 12]

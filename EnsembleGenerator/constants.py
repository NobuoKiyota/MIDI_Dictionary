
# Scale definitions
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]          # Natural Minor
HARMONIC_MINOR_SCALE = [0, 2, 3, 5, 7, 8, 11] # Harmonic Minor (Raised 7th)
MELODIC_MINOR_SCALE = [0, 2, 3, 5, 7, 9, 11]  # Melodic Minor (Ascending)

# Chord Qualities for Diatonic Scales (Index 0 = Degree 1)
# 7th Chords
MAJOR_7TH_QUALITIES = ["M7", "m7", "m7", "M7", "7", "m7", "m7b5"]
MINOR_7TH_QUALITIES = ["m7", "m7b5", "M7", "m7", "m7", "M7", "7"] 
HARMONIC_MINOR_7TH_QUALITIES = ["mM7", "m7b5", "M7#5", "m7", "7", "M7", "dim7"]
MELODIC_MINOR_7TH_QUALITIES = ["mM7", "m7", "M7#5", "7", "7", "m7b5", "m7b5"]


CHORD_INTERVALS = {
    "": [0, 4, 7],         # Major Triad
    "m": [0, 3, 7],        # Minor Triad
    "dim": [0, 3, 6],      # Diminished
    "aug": [0, 4, 8],      # Augmented
    "M7": [0, 4, 7, 11],   # Major 7
    "m7": [0, 3, 7, 10],   # Minor 7
    "7": [0, 4, 7, 10],    # Dominant 7
    "m7b5": [0, 3, 6, 10], # Half Diminished
    "dim7": [0, 3, 6, 9],  # Diminished 7
    "mM7": [0, 3, 7, 11],  # Minor Major 7
    "M7#5": [0, 4, 8, 11], # Augmented Major 7
    # Tensions (5-note chords or 4-note + tension)
    "M9": [0, 4, 7, 11, 14],   # Major 9
    "m9": [0, 3, 7, 10, 14],   # Minor 9
    "9": [0, 4, 7, 10, 14],    # Dominant 9
    "7(b9)": [0, 4, 7, 10, 13], # Dom 7 b9
    "m11": [0, 3, 7, 10, 17],  # Minor 11 (Omit 9 if clash? Or 1-b3-5-b7-11)
    "M7(11)": [0, 4, 7, 11, 17], # Major 7 (11) - usually avoid, but defined for consistency
    "m7(11)": [0, 3, 7, 10, 17], # Same as m11
    "m7b5(11)": [0, 3, 6, 10, 17], # Half Dim 11
    "M7(#11)": [0, 4, 7, 11, 18], # Lydian
}

# Available Tension Mappings (Index 0 = Degree 1)
# Major Scale: 
# I(M7) -> 9 (M9)
# ii(m7) -> 9 (m9)
# iii(m7) -> 11 (m11) [Avoid b9=F]
# IV(M7) -> 9/#11? Lydian #11 is standard but 9 is safe. Let's use M9 for IV.
# V(7) -> 9 (Dom9)
# vi(m7) -> 9 (m9)
# vii(m7b5) -> 11 (m7b5(11)) [Avoid b9=C]
MAJOR_TENSION_SUFFIXES = ["M9", "m9", "m11", "M9", "9", "m9", "m7b5(11)"]

# Natural Minor (Aeolian):
# i(m7) -> 9 (m9)
# ii(m7b5) -> 11 (m7b5(11)) [Locrian, avoid b9]
# III(M7) -> 9 (M9)
# iv(m7) -> 11 (m11) [Phrygian implies b9 avoid? Wait. iv is Dm7 in Am. Key C=Am. Dm7->G7. Dm7 is Dorian relative to C? No, Natural Minor.
# In A Natural Minor: iv=Dm. Scale=A,B,C,D,E,F,G. Dm=D,F,A,C. Tension? E (9th, Interval 14 from D). F is b3. E is Major 9th. Safe is 9.
# Let's check: D(0), F(3), A(7), C(10). E is 2 or 14. D->E is Major 2nd. So m9 is OK.
# v(m7) -> m11? Key Am. v=Em. E,G,B,D. Scale: F (b9). Avoid F. Use 11 (A). So m11.
# VI(M7) -> M9. (FMaj7. G is 9. OK).
# VII(7) -> 7. (G7). A is 9. OK. Dom9.
MINOR_TENSION_SUFFIXES = ["m9", "m7b5(11)", "M9", "m9", "m11", "M9", "9"] 

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def get_note_name(note_number):
    return NOTE_NAMES[note_number % 12]

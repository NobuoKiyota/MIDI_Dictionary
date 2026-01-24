from registries import register_chord
from base_strategies import ChordStrategy
from constants import MAJOR_SCALE, MINOR_SCALE, HARMONIC_MINOR_SCALE, MELODIC_MINOR_SCALE

@register_chord("Maj")
class MajorTriadStrategy(ChordStrategy):
    def get_notes(self, root_note_number, key_info=None):
        # Shift +1 octave for visibility
        base = root_note_number + 12
        return [base, base + 4, base + 7]

@register_chord("Maj_Open")
class MajorTriadOpenStrategy(ChordStrategy):
    def get_notes(self, root_note_number, key_info=None):
        # Root, 5th, 3rd(+oct)
        base = root_note_number + 12
        return [base, base + 7, base + 4 + 12]

@register_chord("Diatonic")
class DiatonicTriadStrategy(ChordStrategy):
    def _get_triad_notes(self, root_note_number, key_info):
        base = root_note_number + 12
        if not key_info:
            return base, base + 4, base + 7 # Fallback
            
        key_root, scale_type = key_info
        
        if scale_type == 'Major':
            scale_intervals = MAJOR_SCALE
        elif scale_type == 'Harmonic Minor':
            scale_intervals = HARMONIC_MINOR_SCALE
        elif scale_type == 'Melodic Minor':
            scale_intervals = MELODIC_MINOR_SCALE
        else: # Default 'Minor' or 'Natural Minor'
            scale_intervals = MINOR_SCALE
            
        scale_notes = [(key_root + i) % 12 for i in scale_intervals]
        
        bass_pitch_class = root_note_number % 12
        if bass_pitch_class not in scale_notes:
            return base, base + 4, base + 7 # Fallback
            
        degree_idx = scale_notes.index(bass_pitch_class)
        third_idx = (degree_idx + 2) % 7
        fifth_idx = (degree_idx + 4) % 7
        
        third_pitch_class = scale_notes[third_idx]
        fifth_pitch_class = scale_notes[fifth_idx]
        
        # Calculate pitches
        third_note = base + 3
        while third_note % 12 != third_pitch_class:
            third_note += 1
            if third_note > base + 6: third_note -= 12
            
        fifth_note = base + 6
        while fifth_note % 12 != fifth_pitch_class:
            fifth_note += 1
            
        return base, third_note, fifth_note

    def get_notes(self, root_note_number, key_info=None):
        r, t, f = self._get_triad_notes(root_note_number, key_info)
        # Ensure order R < 3 < 5 for closed
        if t < r: t += 12
        if f < t: f += 12
        return [r, t, f]

@register_chord("Diatonic_Open")
class DiatonicTriadOpenStrategy(DiatonicTriadStrategy):
    def get_notes(self, root_note_number, key_info=None):
        r, t, f = self._get_triad_notes(root_note_number, key_info)
        # Open: Root, 5th, 3rd(+octave)
        # Ensure 5th is above root
        if f < r: f += 12
        # Ensure 3rd is above 5th? Usually Open Triad is R - 5 - 3(oct)
        # So t needs to be pushed up
        if t < f: t += 12
        
        return [r, f, t]

@register_chord("Diatonic_7th")
class Diatonic7thStrategy(DiatonicTriadStrategy):
    def get_notes(self, root_note_number, key_info=None):
        r, t, f = self._get_triad_notes(root_note_number, key_info)
        
        base = root_note_number + 12
        if not key_info:
            return [base, base+4, base+7, base+11] # Fallback Maj7
            
        key_root, scale_type = key_info
        
        if scale_type == 'Major':
            scale_intervals = MAJOR_SCALE
        elif scale_type == 'Harmonic Minor':
            scale_intervals = HARMONIC_MINOR_SCALE
        elif scale_type == 'Melodic Minor':
            scale_intervals = MELODIC_MINOR_SCALE
        else: # Default 'Minor' or 'Natural Minor'
            scale_intervals = MINOR_SCALE
            
        scale_notes = [(key_root + i) % 12 for i in scale_intervals]
        bass_pitch_class = root_note_number % 12
        
        if bass_pitch_class not in scale_notes:
             return [base, base+4, base+7, base+10] # Fallback Dom7?
             
        degree_idx = scale_notes.index(bass_pitch_class)
        # 7th is degree + 6 indices away (or -1)
        seventh_idx = (degree_idx + 6) % 7
        seventh_pitch_class = scale_notes[seventh_idx]
        
        sev_note = f + 2 # Start search above 5th
        while sev_note % 12 != seventh_pitch_class:
            sev_note += 1
            
        return [r, t, f, sev_note]

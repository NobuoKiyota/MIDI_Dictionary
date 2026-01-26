
from constants import (
    MAJOR_SCALE, MINOR_SCALE, HARMONIC_MINOR_SCALE, MELODIC_MINOR_SCALE,
    MAJOR_7TH_QUALITIES, MINOR_7TH_QUALITIES, 
    HARMONIC_MINOR_7TH_QUALITIES, MELODIC_MINOR_7TH_QUALITIES,
    MAJOR_TENSION_SUFFIXES, MINOR_TENSION_SUFFIXES,
    CHORD_INTERVALS,
    get_note_name
)

# Triad Qualities (Suffixes)
# Index 0 = Degree 1
# Major Scale: I(Maj), ii(m), iii(m), IV(Maj), V(Maj), vi(m), vii(dim)
MAJOR_TRIAD_SUFFIXES = ["", "m", "m", "", "", "m", "dim"] 
# Natural Minor: i(m), ii(dim), III(Maj), iv(m), v(m), VI(Maj), VII(Maj)
MINOR_TRIAD_SUFFIXES = ["m", "dim", "", "m", "m", "", ""]
# Harmonic Minor: i(m), ii(dim), III(Aug), iv(m), V(Maj), VI(Maj), vii(dim)
HARMONIC_MINOR_TRIAD_SUFFIXES = ["m", "dim", "aug", "m", "", "", "dim"]
# Melodic Minor (Asc): i(m), ii(m), III(aug), IV(Maj), V(Maj), vi(dim), vii(dim)
MELODIC_MINOR_TRIAD_SUFFIXES = ["m", "m", "aug", "", "", "dim", "dim"]

class ExpansionStrategy:
    def get_iterations(self, key_info):
        """
        Returns list of tuples: (degree_idx, root_pitch_class, note_name, quality_suffix)
        """
        raise NotImplementedError

class DiatonicTriadStrategy(ExpansionStrategy):
    def get_iterations(self, key_info):
        key_root = key_info[0]
        scale_type = key_info[1]
        
        if scale_type == 'Major':
            intervals = MAJOR_SCALE
            qualities = MAJOR_TRIAD_SUFFIXES
        elif scale_type == 'Harmonic Minor':
             intervals = HARMONIC_MINOR_SCALE
             qualities = HARMONIC_MINOR_TRIAD_SUFFIXES
        elif scale_type == 'Melodic Minor':
             intervals = MELODIC_MINOR_SCALE
             qualities = MELODIC_MINOR_TRIAD_SUFFIXES
        else: # Minor
            intervals = MINOR_SCALE
            qualities = MINOR_TRIAD_SUFFIXES
            
        iterations = []
        for i, interval in enumerate(intervals):
            root_pc = (key_root + interval) % 12
            r_name = get_note_name(root_pc)
            suffix = qualities[i]
            iterations.append({
                'degree': i + 1,
                'root_offset': interval, # From Key Root
                'chord_name': f"{r_name}{suffix}",
                'degree': i + 1,
                'root_offset': interval, # From Key Root
                'chord_name': f"{r_name}{suffix}",
                'type': 'Triad',
                'chord_intervals': CHORD_INTERVALS.get(suffix, [0, 4, 7])
            })
        return iterations

class Diatonic7thStrategy(ExpansionStrategy):
    def get_iterations(self, key_info):
        key_root = key_info[0]
        scale_type = key_info[1]
        
        if scale_type == 'Major':
            intervals = MAJOR_SCALE
            qualities = MAJOR_7TH_QUALITIES
        elif scale_type == 'Harmonic Minor':
             intervals = HARMONIC_MINOR_SCALE
             qualities = HARMONIC_MINOR_7TH_QUALITIES
        elif scale_type == 'Melodic Minor':
             intervals = MELODIC_MINOR_SCALE
             qualities = MELODIC_MINOR_7TH_QUALITIES
        else: # Minor
            intervals = MINOR_SCALE
            qualities = MINOR_7TH_QUALITIES
            
        iterations = []
        for i, interval in enumerate(intervals):
            root_pc = (key_root + interval) % 12
            r_name = get_note_name(root_pc)
            suffix = qualities[i]
            iterations.append({
                'degree': i + 1,
                'root_offset': interval,
                'chord_name': f"{r_name}{suffix}",
                'degree': i + 1,
                'root_offset': interval,
                'chord_name': f"{r_name}{suffix}",
                'type': '7th',
                'chord_intervals': CHORD_INTERVALS.get(suffix, [0, 4, 7, 10])
            })
        return iterations

class HarmonicMinorStrategy(ExpansionStrategy):
    """Effectively same as Diatonic7th but forces Harmonic Minor scale regardless of input key type (if we want to 'force' it)"""
    def get_iterations(self, key_info):
        key_root = key_info[0]
        # FORCE Harmonic Minor
        intervals = HARMONIC_MINOR_SCALE
        qualities = HARMONIC_MINOR_7TH_QUALITIES
        
        iterations = []
        for i, interval in enumerate(intervals):
            root_pc = (key_root + interval) % 12
            r_name = get_note_name(root_pc)
            suffix = qualities[i]
            iterations.append({
                'degree': i + 1,
                'root_offset': interval,
                'chord_name': f"{r_name}{suffix}",
                'degree': i + 1,
                'root_offset': interval,
                'chord_name': f"{r_name}{suffix}",
                'type': 'HarmonicMinor',
                'chord_intervals': CHORD_INTERVALS.get(suffix, [0, 4, 7, 10])
            })
        return iterations

class MelodicMinorStrategy(ExpansionStrategy):
    """Forces Melodic Minor"""
    def get_iterations(self, key_info):
        key_root = key_info[0]
        intervals = MELODIC_MINOR_SCALE
        qualities = MELODIC_MINOR_7TH_QUALITIES
        
        iterations = []
        for i, interval in enumerate(intervals):
            root_pc = (key_root + interval) % 12
            r_name = get_note_name(root_pc)
            suffix = qualities[i]
            iterations.append({
                'degree': i + 1,
                'root_offset': interval,
                'chord_name': f"{r_name}{suffix}",
                'degree': i + 1,
                'root_offset': interval,
                'chord_name': f"{r_name}{suffix}",
                'type': 'MelodicMinor',
                'chord_intervals': CHORD_INTERVALS.get(suffix, [0, 4, 7, 10])
            })
        return iterations

class DiatonicTensionStrategy(ExpansionStrategy):
    """
    Generates chords with Available Tensions (9th/11th) attempting to avoid b9 intervals against chord tones.
    Using predefined mappings in constants.py.
    """
    def get_iterations(self, key_info):
        key_root = key_info[0]
        scale_type = key_info[1]
        
        # Default fallback
        intervals = MAJOR_SCALE
        qualities = MAJOR_TENSION_SUFFIXES
        
        if scale_type == 'Major':
            intervals = MAJOR_SCALE
            qualities = MAJOR_TENSION_SUFFIXES
        elif scale_type == 'Harmonic Minor':
             # Fallback to Minor logic or define Harmonic specific?
             # For now, use Minor logic but Harmonic Scale intervals
             intervals = HARMONIC_MINOR_SCALE
             qualities = MINOR_TENSION_SUFFIXES 
        elif scale_type == 'Melodic Minor':
             intervals = MELODIC_MINOR_SCALE
             qualities = MINOR_TENSION_SUFFIXES
        else: # Minor (Natural)
            intervals = MINOR_SCALE
            qualities = MINOR_TENSION_SUFFIXES
            
        iterations = []
        for i, interval in enumerate(intervals):
            root_pc = (key_root + interval) % 12
            r_name = get_note_name(root_pc)
            
            # Safety for index out of bounds
            if i < len(qualities):
                suffix = qualities[i]
            else:
                suffix = "9" # Default fallback
            
            iterations.append({
                'degree': i + 1,
                'root_offset': interval,
                'chord_name': f"{r_name}{suffix}",
                'type': 'Tension',
                'chord_intervals': CHORD_INTERVALS.get(suffix, [0, 4, 7, 10, 14])
            })
        return iterations

